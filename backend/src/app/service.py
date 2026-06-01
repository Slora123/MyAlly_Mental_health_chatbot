"""
src/app/service.py
───────────────────
Section 12 of the Implementation Guide: Backend responsibilities.

Orchestrates the full query-time RAG pipeline:
  1. Pre-generation safety check  →  crisis path if high-risk
  2. Intent classification          →  router.py
  3. Empathy retrieval              →  retriever.py
  4. Conditional knowledge retrieval
  5. Prompt assembly                →  prompt_builder.py
  6. LLM generation                 →  huggingface_hub InferenceClient
  7. Post-generation safety check   →  safety.py
  8. Logging                        →  app/logging.py
"""

from __future__ import annotations

import os

import chromadb
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from src.app import logging as app_logging
from src.rag import retriever, prompt_builder, router, safety, memory_extractor
from src.rag.embeddings import get_embedding_function
from src.app import vector_db as app_vector_db

from pathlib import Path
root_env = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=root_env)

# ── Config ────────────────────────────────────────────────────────────────────
# Check for both HUGGINGFACE_TOKEN and HUGGINGFACE_API_TOKEN (HF Space default)
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
# Using Qwen2.5-7B-Instruct as requested. (Note: May have cold-start delays on free HF Inference API)
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
DB_PATH = str((
    __import__("pathlib").Path(__file__).resolve().parents[3] / "database" / "chroma_db"
))
EMPATHY_COLLECTION_NAME = "student_support_empathy"
KNOWLEDGE_COLLECTION_NAME = "student_support_knowledge"


def _ensure_hf_token() -> None:
    if not HF_TOKEN:
        raise RuntimeError(
            "HUGGINGFACE_TOKEN is missing. Add it to a .env file before running."
        )


# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_client: InferenceClient | None = None
_empathy_col: chromadb.Collection | None = None
_knowledge_col: chromadb.Collection | None = None


def _get_client() -> InferenceClient:
    global _client
    if _client is None:
        _ensure_hf_token()
        # Added a 15-second timeout to prevent the app from hanging forever during cold starts
        _client = InferenceClient(model=MODEL_NAME, token=HF_TOKEN, timeout=15)
    return _client


def _get_collections() -> tuple[chromadb.Collection, chromadb.Collection]:
    global _empathy_col, _knowledge_col
    if _empathy_col is None or _knowledge_col is None:
        chroma = chromadb.PersistentClient(path=DB_PATH)
        ef = get_embedding_function()
        _empathy_col = chroma.get_or_create_collection(
            name=EMPATHY_COLLECTION_NAME, embedding_function=ef
        )
        _knowledge_col = chroma.get_or_create_collection(
            name=KNOWLEDGE_COLLECTION_NAME, embedding_function=ef
        )
    return _empathy_col, _knowledge_col


def _is_index_empty(empathy_col: chromadb.Collection, knowledge_col: chromadb.Collection) -> bool:
    return empathy_col.count() == 0 or knowledge_col.count() == 0


# ── Main chat logic ───────────────────────────────────────────────────────────

def chat_logic(user_message: str, history: list, user_profile=None, today=None) -> str:
    """
    Full RAG pipeline entry-point consumed by the FastAPI ChatInterface.

    Parameters
    ----------
    user_message : The student's current message.
    history      : Conversation history list of [user, bot] pairs.
    user_profile : The user's database profile object.

    Returns
    -------
    The assistant reply string.
    """
    from datetime import datetime as _dt
    if today is None:
        today = _dt.utcnow()

    empathy_col, knowledge_col = _get_collections()

    # ── Step 1: Pre-generation safety check ──────────────────────────────────
    is_safe, _ = safety.check_pre_generation(user_message)
    intent = router.classify_intent(user_message)

    if not is_safe or intent == "high_risk":
        client = _get_client()
        is_genuine, summary = safety.evaluate_crisis_severity(client, user_message, history)
        
        if is_genuine:
            import random
            from src.app import counselor_service
            name = user_profile.get('nickname') or user_profile.get('name', "bro")
            email = user_profile.get('email', "No email")
            phone = user_profile.get('phone', "No phone provided")
            user_info = f"{name} (Email: {email}, Phone: {phone})"
            
            # Share ONLY the trigger message for context, no history as per privacy request
            counselor_service.save_crisis_alert(summary, user_info=user_info, trigger_message=user_message)
            
            _REPLIES = [
                f"Listen {name}, I need you to stay strong for me right now. I know it feels like the world is crashing down, but you've got a lot of fight in you, and I'm not going to let you face this alone. We're going to get through this together. Can you do me a huge favor and reach out to someone real—a friend, a parent, or a counselor—right this second? If it's too heavy, call a crisis line immediately. You're a warrior, and your story isn't over yet. Who's the first person we're calling?",
                f"Hey {name}, look at me. I hear that pain, but I also know you're stronger than you feel right now. Don't let the darkness win tonight. I'm standing right here with you, and I need you to stay safe and fight through this. Reach out to someone who can be there in person, or hit up a crisis line immediately. You've got so much more to do, and I'm not letting you go. Is there a friend or counselor we can talk to right now?",
                f"{name.capitalize()}, stay with me. You're going through a storm, but storms don't last forever. I'm your ally, and I'm telling you to hold on and be strong. You have the strength to get through this, even if it doesn't feel like it. Please, reach out to a professional or a trusted person immediately. Promise me you'll fight this and talk to someone real. You matter way too much to give up. Who is one person you can reach out to right now?"
            ]
            crisis_reply = random.choice(_REPLIES)
            
            app_logging.append_log(
                app_logging.make_log_entry(
                    user_query=user_message,
                    ai_response=crisis_reply,
                    intent="high_risk",
                    retrieved_empathy_ids=[],
                    retrieved_knowledge_ids=[],
                    retrieved_empathy_metadata=[],
                    retrieved_knowledge_metadata=[],
                    mode="crisis_escalated",
                )
            )
            return crisis_reply
        else:
            # The LLM evaluated this as 'playing' or not genuinely dangerous.
            # We override the high-risk block and proceed normally as "support_only".
            is_safe = True
            intent = "support_only"

    # ── Step 1.5: Extract & persist life events from user message ───────────────
    uid = user_profile.get("uid") if user_profile else None
    if uid:
        detected = memory_extractor.extract_events(user_message, today=today)
        if detected:
            app_vector_db.update_life_events(uid, detected)

    # ── Step 1.7: Build proactive context from stored life events ─────────────
    proactive_ctx = None
    if uid:
        life_events = app_vector_db.get_life_events(uid)
        proactive_ctx = memory_extractor.get_proactive_context(life_events, today=today)

    # ── Step 1.8: Retrieve relevant past memories + recent context ────────────
    relevant_memories: list[str] = []
    recent_memories: list[str] = []
    if uid:
        relevant_memories = app_vector_db.get_relevant_memories(uid, user_message, top_n=3)
        recent_memories = app_vector_db.get_recent_memories(uid, limit=5)

    # ── Step 2: Retrieval ─────────────────────────────────────────────────────
    # If the RAG index is empty (e.g. local dev without datasets), skip retrieval
    # gracefully and let the LLM respond without context documents.
    rag_available = not _is_index_empty(empathy_col, knowledge_col)
    if not rag_available:
        print("⚠️  [service] RAG index is empty — running in LLM-only mode (no empathy/knowledge context).")

    if intent == "greeting" or not rag_available:
        # Skip intensive retrieval for greetings or when index is empty
        empathy_items = []
        knowledge_items = []
    else:
        empathy_items = retriever.retrieve_empathy_examples(empathy_col, user_message, top_n=2)

        fetch_knowledge = intent in ("knowledge_seeking", "mixed")
        knowledge_items = (
            retriever.retrieve_knowledge_snippets(knowledge_col, user_message)
            if fetch_knowledge
            else []
        )

    # ── Step 3: Prompt assembly ───────────────────────────────────────────────
    empathy_ctx = retriever.render_empathy_context(empathy_items)
    knowledge_ctx = retriever.render_knowledge_context(knowledge_items)
    messages = prompt_builder.build_messages(
        user_message, history, empathy_ctx, knowledge_ctx, user_profile,
        proactive_context=proactive_ctx,
        relevant_memories=relevant_memories,
        recent_memories=recent_memories,
    )

    # ── Step 4: Generation ────────────────────────────────────────────────────
    try:
        response = _get_client().chat_completion(
            messages=messages,
            max_tokens=250,  # Reduced from 400 for 40% faster generation
            temperature=0.7,
        )
        ai_reply: str = " ".join(
            response.choices[0].message.content.split()
        )
    except Exception as e:
        return f"Model error: {e}"

    # ── Step 4.5: Store this message as a long-term memory AFTER retrieval ──
    if uid and memory_extractor.should_store_memory(user_message):
        app_vector_db.add_user_memory(uid, user_message)
        print(f"🧠 Memory stored for {uid}: {user_message[:60]}...")

    # ── Step 5: Post-generation safety check ─────────────────────────────────
    reply_safe, safety_issues = safety.check_post_generation(ai_reply)
    # Log issues but do not block: add a gentle disclaimer instead
    if not reply_safe:
        ai_reply += (
            "\n\n_(Please remember: I'm a support assistant, not a therapist or "
            "medical professional. For clinical advice, reach out to a qualified "
            "professional.)_"
        )

    # ── Step 6: Logging ───────────────────────────────────────────────────────
    app_logging.append_log(
        app_logging.make_log_entry(
            user_query=user_message,
            ai_response=ai_reply,
            intent=intent,
            retrieved_empathy_ids=[item["id"] for item in empathy_items],
            retrieved_knowledge_ids=[item["id"] for item in knowledge_items],
            retrieved_empathy_metadata=[item["metadata"] for item in empathy_items],
            retrieved_knowledge_metadata=[item["metadata"] for item in knowledge_items],
            safety_issues=safety_issues,
            mode="support_plus_rag" if rag_available else "llm_only",
        )
    )

    return ai_reply
