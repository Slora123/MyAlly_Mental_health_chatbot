"""
src/rag/safety.py
──────────────────
Section 11 of the Implementation Guide: Safety Layer.

Two functions:
  check_pre_generation(message)  → (is_safe, reason)
  check_post_generation(reply)   → (is_safe, list_of_issues)

Pre-generation is a fast gate before any retrieval or generation.
Post-generation reviews the model's reply before it reaches the user.
"""

from __future__ import annotations

from src.rag.router import is_high_risk

# ── Post-generation red-flag patterns ─────────────────────────────────────────
# Each entry is (description, list_of_trigger_phrases).
# Phrase matching is case-insensitive on normalised text.

_DIAGNOSIS_PATTERNS: list[str] = [
    "you have depression",
    "you have anxiety",
    "you are depressed",
    "you are anxious",
    "you definitely have",
    "you clearly have",
    "you suffer from",
    "you are diagnosed",
    "i diagnose",
    "this is a diagnosis",
    "based on your symptoms you have",
]

_MEDICATION_PATTERNS: list[str] = [
    "stop taking your medication",
    "stop taking your medicine",
    "stop your medication",
    "don't take your medication",
    "do not take your medication",
    "take more",
    "increase your dose",
    "decrease your dose",
    "change your prescription",
    "you should stop your antidepressant",
    "you should stop your pills",
]

_DISMISSIVE_PATTERNS: list[str] = [
    "just get over it",
    "stop being dramatic",
    "you're overreacting",
    "you are overreacting",
    "it's not a big deal",
    "it is not a big deal",
    "everyone feels that way",
    "just be positive",
    "just think happy thoughts",
    "you should be grateful",
    "others have it worse",
    "stop being weak",
    "man up",
    "grow up",
]

_CERTAINTY_PATTERNS: list[str] = [
    "i am certain that",
    "100 percent sure",
    "guaranteed to",
    "this will definitely cure",
    "this will definitely fix",
    "scientifically proven that you",
    "there is no doubt",
    "you will definitely feel better if you",
]

_UNSAFE_ADVICE_PATTERNS: list[str] = [
    "ignore those thoughts",
    "just ignore the urge",
    "ignore thoughts of suicide",
    "you don't need a therapist",
    "you do not need a therapist",
    "therapy is not for you",
    "you don't need help",
    "you do not need help",
]


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


def _find_matches(norm_text: str, patterns: list[str]) -> list[str]:
    return [p for p in patterns if p in norm_text]


# ── Public API ────────────────────────────────────────────────────────────────


def check_pre_generation(message: str) -> tuple[bool, str]:
    """
    Pre-generation safety gate (Section 11 – Pre-generation checks).

    Returns
    -------
    (True, "")            – message is safe to proceed with normal RAG flow
    (False, reason_str)   – message requires special handling (crisis path)
    """
    if is_high_risk(message):
        return False, "high_risk_signal_detected"
    return True, ""


def check_post_generation(reply: str) -> tuple[bool, list[str]]:
    """
    Post-generation safety review (Section 11 – Post-generation checks).

    Checks the model's reply for:
      - Diagnosis claims
      - Unsafe medication advice
      - Dismissive or blaming language
      - Unsafe advice (e.g. "ignore those thoughts")
      - Excessive certainty overclaiming

    Returns
    -------
    (True, [])            – reply passed all checks
    (False, [issue_list]) – reply failed one or more checks; caller should
                            log the issues and either warn or regenerate.
    """
    norm = _normalise(reply)
    issues: list[str] = []

    if _find_matches(norm, _DIAGNOSIS_PATTERNS):
        issues.append("diagnosis_claim_detected")

    if _find_matches(norm, _MEDICATION_PATTERNS):
        issues.append("unsafe_medication_advice_detected")

    if _find_matches(norm, _DISMISSIVE_PATTERNS):
        issues.append("dismissive_or_blaming_language_detected")

    if _find_matches(norm, _UNSAFE_ADVICE_PATTERNS):
        issues.append("unsafe_advice_detected")

    if _find_matches(norm, _CERTAINTY_PATTERNS):
        issues.append("certainty_overclaiming_detected")

    return (len(issues) == 0), issues


def evaluate_crisis_severity(client, user_message: str, history: list) -> tuple[bool, str]:
    """
    Uses the provided LLM client to evaluate if the high-risk message constitutes
    a genuine and continuous crisis vs 'playing around'.
    
    Returns
    -------
    (is_genuine_crisis: bool, summary: str)
    """
    system_prompt = (
        "You are a crisis evaluation system. A user has triggered a high-risk keyword. "
        "Review their recent chat history and the latest message.\n"
        "1) If the user is genuinely expressing persistent or continuous extreme stress or suicidal intent, "
        "reply with 'ESCALATE', followed by double newline, followed by a short 2-3 sentence summary of the crisis directly quoting the user context.\n"
        "2) If the user appears to be joking, playing around, testing the bot, or not in genuine extreme distress, "
        "reply with 'IGNORE'.\n"
    )
    
    history_text = ""
    if history:
        history_text = "\n".join([f"User: {u}\nBot: {b}" for u, b in history[-4:]])  # Look at last 4 turns
        
    user_prompt = f"Chat History:\n{history_text}\nLatest Message: {user_message}\nEvaluate now."
    
    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=60, # Reduced from 150 for much faster classification
            temperature=0.0
        )
        reply = response.choices[0].message.content.strip()
        if reply.startswith("ESCALATE"):
            parts = reply.split("\n\n", 1)
            summary = parts[1] if len(parts) > 1 else f"User expressed intent to self-harm: {user_message}"
            return True, summary.strip()
        else:
            return False, ""
    except Exception as e:
        print(f"Error evaluating crisis: {e}")
        # Default to safe side if LLM evaluation fails
        return True, f"Possible crisis detected (LLM check failed). User said: {user_message}"
