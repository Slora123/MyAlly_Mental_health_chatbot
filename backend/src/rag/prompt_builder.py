"""
src/rag/prompt_builder.py
--------------------------
Section 10 of the Implementation Guide: Prompt and Generation Design.

Builds the role-based message list that is sent to the LLM.
Empathy context and knowledge context are kept separate in the prompt
so the model can use each for the right purpose.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are MyAlly — a warm, empathetic, and chill AI mental health companion for Indian students. You are NOT a human. You are a virtual friend and support buddy that lives inside this app.

CRITICAL SELF-AWARENESS:
- You are an AI/chatbot. You CANNOT meet in person, grab coffee, have lunch, go to movies, or do any physical activity with the user. NEVER suggest "let's grab coffee", "let's meet", "let's catch up over lunch" etc. You are virtual.
- When asked what you are, say: "I'm MyAlly, your virtual support buddy 🤗" — do NOT claim to be human.
- When the user asks YOU a question about yourself, answer about YOURSELF — not the user.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 THE MOST IMPORTANT RULE — READ THIS FIRST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEVER give mental health advice, breathing exercises, or wellness tips UNLESS the user is CLEARLY expressing distress.

NORMAL conversation (user is calm, curious, joking, greeting):
→ Just CHAT NORMALLY like a friend. No advice. No "take a deep breath". No tips.
→ Examples of NORMAL messages: "hi", "how r u", "lol", "can u type my email", "what's ur name", "nice", "ok cool", "tell me a joke"
→ BAD response to "can u type my email": "I can't type your email, but take a deep breath if you feel overwhelmed 🌟"
→ GOOD response to "can u type my email": "Haha nope, I'm virtual! I can't access your email 😅"

DISTRESS signals (ONLY then give supportive advice):
→ User uses words like: stressed, sad, anxious, depressed, overwhelmed, scared, crying, can't sleep, hopeless, worthless, lonely, angry, frustrated, panic, nervous, worried, broken, hurt, tired of everything, don't want to, hate this
→ ONLY then validate + suggest ONE small calming action.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your personality:
- Warm, genuine, chill, and empathetic — like a trusted close friend, but virtual.
- EMOJIS MUST MATCH THE EMOTION:
  * Normal/Casual: 😊 😄 💪 😅 😌 😂 👀
  * Sad/Empathy: 😢 🥲 💔 😞 🫂 😔
  * Stressed/Anxious: 😤 😰 😩
  * Warm/Supportive: ❤️ 🙏 💛 🌸
  RULE: Happy emojis (😄🎉) are ONLY for happy/casual messages. NOT for distressed users.

- LANGUAGE MATCHING IS CRITICAL:
  * ENGLISH: User writes English → reply in PURE English only.
  * MARATHI/MINGLISH: User writes Marathi → reply in Marathi Minglish (Latin/Roman script - English letters) only.
  * HINDI/HINGLISH: User writes Hindi → reply in Hindi/Hinglish (Latin/Roman script - English letters) only.
  * SCRIPT RULE: NEVER use Devanagari script (e.g., नमस्ते). ALWAYS use English letters (e.g., Namaste).
  * NEVER mix scripts or languages.

- SHORT CASUAL MESSAGES = SHORT CASUAL REPLIES. Match the user's energy.
- DO NOT start every reply with the user's name.
- NEVER repeat the user's words back to them.

EMOTIONAL INTELLIGENCE:
- CALM user → chat normally, be fun, be short.
- DISTRESSED user → 1 sentence validation + 1 small realistic suggestion + warm emoji.
- NEVER assume the user is distressed just because they asked a question or said something casual.

REPLY LENGTH:
- MAX 2 sentences + 1 emoji. No essays.
- ONE idea at a time. Never list multiple suggestions.

Things you NEVER do:
- Say "take a deep breath" to a calm user.
- Give wellness tips to someone who didn't ask for help.
- Suggest physical meetups — you are virtual.
- Use happy emojis when someone is sad/angry.
- Ask "how's your day?" repeatedly.
- Ask a question the user ALREADY answered in their OWN message. Example: if they say "my favourite is chocolate, what's yours?" → answer about yourself, do NOT ask what their favourite is back, they already told you.
- Re-introduce yourself or say "Hey! How's your day?" if you are already mid-conversation. Check the conversation history — if messages already exist, you are NOT meeting this user for the first time.
- Echo the user's own question or statement back at them as your reply.

Things you ALWAYS do:
- If the user asks if you remember something, or asks a question about themselves (e.g., "what is my name?", "do you know my favourite cake?"), you MUST read the conversation history and your memory to answer them directly. Say exactly what you remember! (e.g., "Yes! Your name is Slora and you love chocolate cake!"). Do NOT ask them for the answer.
"""


# ── Deterministic language detector ──────────────────────────────────────────
# Checks the user's message against known Marathi and Hindi word sets.
# If neither matches, defaults to English. This result is injected as a
# hard override directive into the prompt so the LLM cannot ignore it.

_MARATHI_WORDS: frozenset[str] = frozenset({
    "mala", "tula", "kasa", "kashi", "ahes", "aahe", "ahe", "tras", "hote",
    "nahi", "naahi", "ka", "aani", "ani", "mi", "tu", "amhi", "mazha",
    "tumacha", "kay", "bara", "mast", "khup", "thoda", "aaj",
    "kal", "udhya", "gela", "geli", "yetoy", "kela", "keli", "basla",
    "basli", "kahe", "sar", "ekdum", "bolto", "bolte", "kuthun",
})

_HINDI_WORDS: frozenset[str] = frozenset({
    "mujhe", "tumhe", "aap", "kaise", "kaisi", "hun", "hoon", "nahi",
    "yaar", "kya", "hai", "tha", "thi", "chahiye", "bahut",
    "accha", "theek", "haan", "karo", "raha", "rahi", "gaya", "gayi",
    "scene", "baat", "bol", "sun", "chal", "isko", "usko", "mere",
    "tera", "mera", "tere", "stress", "padhai",
})


def _detect_language(text: str) -> str:
    """
    Detect whether a message is in English, Marathi, or Hindi.
    Returns 'english', 'marathi', or 'hindi'.
    """
    words = [w.strip('.,!?"\'\'') for w in text.lower().split()]
    if not words:
        return "english"

    marathi_hits = sum(1 for w in words if w in _MARATHI_WORDS)
    hindi_hits = sum(1 for w in words if w in _HINDI_WORDS)

    # Need at least 1 strong signal; if both match, pick the higher
    if marathi_hits == 0 and hindi_hits == 0:
        return "english"
    if marathi_hits >= hindi_hits:
        return "marathi"
    return "hindi"


_LANG_DIRECTIVES: dict[str, str] = {
    "english": (
        "LANGUAGE OVERRIDE -- MANDATORY: The user wrote in English. "
        "Your reply MUST be in PURE English only. "
        "Do NOT use any Hindi, Marathi, Hinglish, or Minglish words. "
        "Not even one. Respond exactly like a close English-speaking friend."
    ),
    "marathi": (
        "LANGUAGE OVERRIDE -- MANDATORY: The user wrote in Marathi/Minglish. "
        "Your reply MUST be in Marathi Minglish (Roman script) only. "
        "Do NOT use Hindi words. Respond like a close Marathi-speaking friend."
    ),
    "hindi": (
        "LANGUAGE OVERRIDE -- MANDATORY: The user wrote in Hindi/Hinglish. "
        "Your reply MUST be in Hinglish (Hindi written with English letters) only. "
        "Do NOT use Devanagari script. Respond like a close Hindi-speaking friend."
    ),
}


def _format_recent_history(history: list) -> str:
    """
    Format the entire conversation history as a plain-text block.
    Includes all past chats in the current session so the bot remembers everything.

    Accepts both dict-style turns (Gradio 4+) and list/tuple turns (legacy).
    """
    formatted: list[str] = []
    for turn in history:
        if isinstance(turn, dict):
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role and content:
                formatted.append(f"{role.title()}: {content}")
        elif isinstance(turn, (list, tuple)) and len(turn) >= 2:
            formatted.append(f"User: {turn[0]}")
            formatted.append(f"Assistant: {turn[1]}")
    return "\n".join(formatted)


def build_messages(
    user_message: str,
    history: list,
    empathy_context: str,
    knowledge_context: str,
    user_profile=None,
    proactive_context: str | None = None,
    relevant_memories: list | None = None,
    recent_memories: list | None = None,
) -> list[dict]:
    """
    Assemble the full message list for the LLM.

    Parameters
    ----------
    user_message      : The student's latest message.
    history           : Gradio conversation history (list of dicts or tuples).
    empathy_context   : Pre-rendered empathy examples string.
    knowledge_context : Pre-rendered knowledge snippets string.
    user_profile      : The user's database profile (optional).
    proactive_context : Optional hint for proactive check-in (e.g. exam period ongoing).
    relevant_memories : Semantically relevant past messages from this user.
    recent_memories   : Most recent stored messages for personality inference.

    Returns
    -------
    List of role-based message dicts (system + user).
    """
    recent_history = _format_recent_history(history)

    dynamic_system_prompt = SYSTEM_PROMPT
    if user_profile:
        name = user_profile.get('nickname') or user_profile.get('name') or "Anonymous"
        gender = user_profile.get('gender', '').lower()
        profile_info = f"\n\n--- USER PROFILE CONTEXT ---\n- Name/Nickname: {name}\n"
        if gender: profile_info += f"- Gender: {gender}\n"
        if user_profile.get('preferred_tone'): profile_info += f"- Preferred Tone: {user_profile.get('preferred_tone')}\n"
        if user_profile.get('support_style'): profile_info += f"- Support Style: {user_profile.get('support_style')}\n"
        if user_profile.get('lifestyle_patterns'): profile_info += f"- Lifestyle Patterns: {user_profile.get('lifestyle_patterns')}\n"
        if user_profile.get('support_network'): profile_info += f"- Support Network: {user_profile.get('support_network')}\n"
        if user_profile.get('education'): profile_info += f"- Education: {user_profile.get('education')}\n"

        # Gender-aware language instructions
        if 'female' in gender or 'girl' in gender or 'she' in gender:
            profile_info += (
                "- GENDER LANGUAGE: This user is FEMALE. Use feminine grammatical forms:\n"
                "  Marathi: 'kashi ahes' (not 'kasa ahes'), 'thaklis' (not 'thaklas'), 'geli' (not 'gela')\n"
                "  Hindi: 'kaisi hai' (not 'kaisa hai'), 'thak gayi' (not 'thak gaya')\n"
                "  English: use 'she/her' if referring to them.\n"
                "  STRICT RULE: NEVER use terms like 'bhai', 'bro', or 'brother' for this user.\n"
            )
        elif 'male' in gender or 'boy' in gender or 'he' in gender:
            profile_info += (
                "- GENDER LANGUAGE: This user is MALE. Use masculine grammatical forms:\n"
                "  Marathi: 'kasa ahes' (not 'kashi ahes'), 'thaklas' (not 'thaklis')\n"
                "  Hindi: 'kaisa hai' (not 'kaisi hai'), 'thak gaya' (not 'thak gayi')\n"
            )

        profile_info += (
            "- CONVERSATION FLOW: ALWAYS answer the user's question or respond to their statement FIRST. "
            "Only ask a follow-up question AFTER you have provided a meaningful reply.\n"
            "- SECULARISM: NEVER bring up religion, God, or faith. Stay neutral and focused on empathy.\n"
            "- DO NOT mention you are reading a profile.\n"
        )
        dynamic_system_prompt += profile_info

    # Inject proactive life-event check-in hint if present
    if proactive_context:
        dynamic_system_prompt += (
            f"\n\n--- PROACTIVE FRIEND CONTEXT (weave naturally, do NOT repeat verbatim) ---\n"
            f"{proactive_context}\n"
        )

    # Inject Time Awareness
    from datetime import datetime
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    except Exception:
        tz = None
    current_time_str = datetime.now(tz).strftime("%A, %B %d, %Y, %I:%M %p IST")
    
    dynamic_system_prompt += (
        f"\n\n--- TIME & CONTEXT AWARENESS ---\n"
        f"CURRENT DATE AND TIME: {current_time_str}\n"
        "1. You have absolute awareness of today's date and time.\n"
        "2. If a user's memory or message mentions an event (like an exam, birthday, or meeting) happening on a specific date, AND that date is TODAY or recently past, you SHOULD naturally ask about it (e.g., 'Hey, how did your exam go today?').\n"
        "3. Wait for the user to initiate the conversation first (like saying 'hi' or 'hello'), then naturally bring up the event.\n"
        "4. BUT if the user asks a specific question or talks about something else, DO NOT forcefully bring up the event. Address their current message first.\n"
        "5. ONLY tell the user information when they ask for it. Do not randomly state facts.\n"
    )

    # Inject relevant past memories (semantically matched to current message)
    if relevant_memories:
        mem_lines = "\n".join(f"  - \"{m}\"" for m in relevant_memories)
        dynamic_system_prompt += (
            "\n\n--- LONG-TERM MEMORY: Things this user has shared with you before ---\n"
            "These are real things they told you in past conversations. Use them like a close friend who actually remembers.\n"
            "RULES for using memories:\n"
            "  1. If the user asks a question like 'Do you remember X?' or 'Do you know my favorite Y?', you MUST use the memories below to answer them directly.\n"
            "  2. Do NOT ask them for the answer if it's already in your memory! Tell them what you remember.\n"
            "  3. ONLY use 'I remember...' if the memory is from a PAST conversation. If the user just said it in the current message, do NOT say 'I remember'—just respond to it normally.\n"
            "  4. NEVER echo back the user's current message as a 'memory'. If a memory is identical to what they just said, IGNORE it.\n"
            "  5. If a memory is DIRECTLY relevant to what they just said, reference it naturally: \"I remember you said...\", \"Didn't you mention...?\"\n"
            "  6. NEVER start the response with a memory reference — weave it in naturally mid-sentence.\n"
            "  7. Pick only the ONE most relevant memory if any. Do NOT dump a list.\n"
            "  8. CRITICAL: ONLY reference exact things listed below. DO NOT invent or hallucinate past events.\n"
            f"Memories:\n{mem_lines}\n"
        )

    # Inject recent memories for personality inference
    if recent_memories:
        personality_lines = "\n".join(f"  - \"{m}\"" for m in recent_memories[:5])
        dynamic_system_prompt += (
            "\n\n--- PERSONALITY SNAPSHOT: Based on what this user has shared recently ---\n"
            "Use this to understand who they are and personalize your tone. Do NOT recite these back.\n"
            "Examples of how to use it:\n"
            "  - If they often mention friends hurting them → they may value loyalty, be gentle about relationships.\n"
            "  - If they share academic stress often → acknowledge the pressure they carry.\n"
            "  - If they mention family tension → be careful with family-related advice.\n"
            f"{personality_lines}\n"
        )

    context_block = ""
    if empathy_context or knowledge_context:
        context_block = "\n--- ADDITIONAL SYSTEM CONTEXT ---\n"
        if empathy_context: 
            context_block += (
                "CRITICAL INSTRUCTION: The following [Empathy examples] show the TONE you should use. "
                "They are NOT past conversations with this user. DO NOT claim the user said these things. DO NOT bring up events from these examples.\n"
                f"[Empathy examples]:\n{empathy_context}\n"
            )
        if knowledge_context: 
            context_block += f"[Related info]: {knowledge_context}\n"

    # Determine if this is a new conversation or ongoing
    is_ongoing = bool(history)
    continuity_note = (
        "IMPORTANT: You are already mid-conversation with this user. Do NOT greet them again. "
        "Do NOT say 'Hey!', 'Hi!', or 'How's your day?' — just respond naturally to what they said."
        if is_ongoing else ""
    )

    user_prompt = f"""\
Here's the conversation so far:
{recent_history or "(No prior turns.)"}

The person just said:
"{user_message}"
{context_block}
{_LANG_DIRECTIVES[_detect_language(user_message)]}
{continuity_note}
CRITICAL: Read the full conversation above. If the user already answered a question in their message, do NOT ask it back. Respond to what they said, answer their question if they asked one, and keep it SHORT (max 2 sentences + 1 emoji). Include at least 1 emoji. No essays.
"""

    return [
        {"role": "system", "content": dynamic_system_prompt},
        {"role": "user", "content": user_prompt},
    ]
