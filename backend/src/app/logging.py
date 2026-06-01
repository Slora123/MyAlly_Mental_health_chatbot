"""
src/app/logging.py
───────────────────
Section 13 of the Implementation Guide: Conversation Memory / Logging.

JSONL logging of every interaction request with:
  - timestamp
  - user_query
  - intent classification
  - retrieved document IDs and metadata
  - ai_response
  - post-generation safety flags (if any)
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
LOG_FILE = BASE_DIR / "rag_reference_logs.jsonl"


def append_log(entry: dict) -> None:
    """Append a single JSONL entry to the log file."""
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def make_log_entry(
    *,
    user_query: str,
    ai_response: str,
    intent: str,
    retrieved_empathy_ids: list[str],
    retrieved_knowledge_ids: list[str],
    retrieved_empathy_metadata: list[dict],
    retrieved_knowledge_metadata: list[dict],
    safety_issues: list[str] | None = None,
    mode: str = "support_plus_rag",
) -> dict:
    """Build a structured log entry dict."""
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_query": user_query,
        "intent": intent,
        "mode": mode,
        "retrieved_empathy_ids": retrieved_empathy_ids,
        "retrieved_knowledge_ids": retrieved_knowledge_ids,
        "retrieved_empathy_metadata": retrieved_empathy_metadata,
        "retrieved_knowledge_metadata": retrieved_knowledge_metadata,
        "ai_response": ai_response,
        "post_gen_safety_issues": safety_issues or [],
    }


def get_ui_history() -> list[list[str]]:
    """
    Read the JSONL log and return a Gradio-compatible history list
    so the chat window can pre-populate with past turns.
    """
    history: list[list[str]] = []
    if not LOG_FILE.exists():
        return history
    with LOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
                user = entry.get("user_query", "")
                bot = entry.get("ai_response", "")
                if user or bot:
                    history.append([user, bot])
            except Exception:
                continue
    return history
