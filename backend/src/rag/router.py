"""
src/rag/router.py
──────────────────
Section 9.1 of the Implementation Guide: Add a lightweight message router.

The four intent categories defined by the guide:
  - high_risk       : self-harm / suicide / immediate danger signals
  - knowledge_seeking: factual mental-health questions
  - mixed           : emotional distress AND a factual question in the same message
  - support_only    : emotional venting / distress with no factual question
"""

from __future__ import annotations

# ── Crisis / high-risk signals ────────────────────────────────────────────────
_CRISIS_PHRASES: frozenset[str] = frozenset(
    {
        "kill myself",
        "want to die",
        "end my life",
        "suicide",
        "suicidal",
        "suiciding",
        "self harm",
        "harm myself",
        "cut myself",
        "cutting myself",
        "overdose",
        "don't want to live",
        "do not want to live",
        "i am unsafe",
        "can't keep going",
        "cannot keep going",
        "no reason to live",
        "thinking about ending",
        "ending everything",
        "hurt myself",
        "take my own life",
        "end it all"
    }
)

# ── Knowledge-seeking signals ─────────────────────────────────────────────────
# These tokens suggest the user wants factual information rather than
# (or in addition to) emotional support.
_KNOWLEDGE_TOKENS: frozenset[str] = frozenset(
    {
        "what",
        "why",
        "how",
        "explain",
        "tell me about",
        "symptom",
        "symptoms",
        "diagnosis",
        "diagnose",
        "depression",
        "anxiety",
        "trauma",
        "ocd",
        "obsessive",
        "treatment",
        "prevent",
        "preventive",
        "therapy",
        "therapist",
        "disorder",
        "medication",
        "medicine",
        "cope",
        "coping",
        "technique",
        "strategy",
    }
)

# ── Emotional distress signals ────────────────────────────────────────────────
# These suggest the user primarily needs emotional support / validation.
_DISTRESS_TOKENS: frozenset[str] = frozenset(
    {
        "feel",
        "feeling",
        "sad",
        "alone",
        "lonely",
        "stressed",
        "stress",
        "overwhelmed",
        "exhausted",
        "tired",
        "burnout",
        "burnt out",
        "homesick",
        "anxious",
        "scared",
        "lost",
        "hopeless",
        "helpless",
        "crying",
        "cry",
        "can't sleep",
        "cannot sleep",
        "worried",
        "worry",
        "nervous",
    }
)


# ── Greeting signals ──────────────────────────────────────────────────────────
_GREETING_TOKENS: frozenset[str] = frozenset(
    {"hi", "hello", "hey", "hola", "namaste", "how are you", "how are u", "kaise ho", "kaisa hai", "kaisi hai", "kaisi hai tu", "kaisa hai tu", "kaise ho aap", "kashi ahes", "kasa ahes", "kashi aahe", "kasa aahe", "kay challay", "kya chal raha", "sup", "wassup", "hai", "kashi", "kasa"}
)


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


def is_high_risk(text: str) -> bool:
    """True if the message contains a crisis / self-harm signal."""
    norm = _normalise(text)
    return any(phrase in norm for phrase in _CRISIS_PHRASES)


def _is_greeting(norm: str) -> bool:
    return any(norm.startswith(token) for token in _GREETING_TOKENS) or norm in _GREETING_TOKENS


def _has_knowledge_signal(norm: str) -> bool:
    # If it's a simple greeting like "how are you", it's not knowledge-seeking
    if _is_greeting(norm) and len(norm.split()) <= 4:
        return False
    return "?" in norm or any(token in norm for token in _KNOWLEDGE_TOKENS)


def _has_distress_signal(norm: str) -> bool:
    return any(token in norm for token in _DISTRESS_TOKENS)


def classify_intent(text: str) -> str:
    """
    Classify the user message into one of five intent categories.

    Returns
    -------
    "high_risk"         – crisis / self-harm language detected
    "greeting"          – simple social greeting
    "knowledge_seeking" – factual question, no strong distress signal
    "mixed"             – both distress and a factual question
    "support_only"      – emotional distress with no factual question
    """
    norm = _normalise(text)

    if is_high_risk(text):
        return "high_risk"

    if _is_greeting(norm) and not _has_distress_signal(norm) and len(norm.split()) <= 5:
        return "greeting"

    has_knowledge = _has_knowledge_signal(norm)
    has_distress = _has_distress_signal(norm)

    if has_knowledge and has_distress:
        return "mixed"
    if has_knowledge:
        return "knowledge_seeking"
    # Default: treat as support-only (emotional validation path)
    return "support_only"
