"""
backend/src/rag/memory_extractor.py
-------------------------------------
Extracts life events (exam dates, deadlines, events) from user messages
and generates proactive check-in context hints for the LLM.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

# ── Memory storage filter ─────────────────────────────────────────────────────
# Keywords that signal the user is sharing something personal and worth storing.
_PERSONAL_SIGNALS = frozenset({
    "my friend", "my best friend", "my friends", "my family", "my mom",
    "my dad", "my mother", "my father", "my sister", "my brother",
    "my boyfriend", "my girlfriend", "my partner", "my teacher", "my prof",
    "my boss", "my crush", "my roommate", "my classmate",
    "i feel", "i felt", "i am", "i'm", "i was", "i have", "i had",
    "i love", "i hate", "i want", "i need", "i think", "i always", "i never",
    "i used to", "i can't", "i couldn't", "i won't", "i don't", "i wish",
    "stressed", "anxious", "depressed", "lonely", "sad", "happy", "angry",
    "scared", "nervous", "worried", "frustrated", "excited", "overwhelmed",
    "college", "school", "exam", "class", "study", "job", "work", "internship",
    "birthday", "anniversary", "breakup", "fight", "argument", "cried",
    "hurt", "betrayed", "ignored", "rejected", "failed", "passed",
})


def should_store_memory(message: str) -> bool:
    """
    Return True if this user message is worth storing as a long-term memory.
    Filters out greetings, one-word replies, and trivial messages.
    """
    cleaned = message.strip()
    if len(cleaned.split()) < 8: # Increased from 6
        return False
    
    msg_lower = cleaned.lower()
    # Check for personal signals
    has_signal = any(signal in msg_lower for signal in _PERSONAL_SIGNALS)
    
    # Avoid storing messages that look like simple repetition or questions
    is_question = cleaned.endswith('?')
    
    return has_signal and not is_question

# Month name mapping (longer names first to avoid partial matches)
MONTHS: dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

EXAM_KEYWORDS: frozenset[str] = frozenset({
    "exam", "exams", "test", "tests", "paper", "papers",
    "finals", "midterm", "midterms", "viva", "assessment", "boards",
})

EVENT_KEYWORDS: frozenset[str] = frozenset({
    "presentation", "interview", "submission", "deadline", "project", "assignment",
})

BIRTHDAY_KEYWORDS: frozenset[str] = frozenset({
    "birthday", "bday", "b-day", "birth day",
    "janamdin", "janmdin",  # Hindi
    "wadhdiws",             # Punjabi
})

# Build month alternation pattern, longest-first to avoid partial matches
_MONTH_ALT = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))


def _build_date(today: datetime, month: int, day: int) -> Optional[str]:
    """Return ISO date string; rolls over to next year if date has passed."""
    try:
        candidate = datetime(today.year, month, day)
        if candidate.date() < today.date():
            candidate = datetime(today.year + 1, month, day)
        return candidate.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_date_str(date_str: str, today: datetime) -> Optional[str]:
    """Convert a natural-language date fragment to ISO YYYY-MM-DD."""
    s = date_str.strip().lower()

    if s in ("today", "aaj", "now"):
        return today.strftime("%Y-%m-%d")
    if s in ("tomorrow", "kal", "tmr", "tmrw"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if s in ("day after tomorrow", "parso"):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")

    # "may 6" / "april 29th"
    m = re.search(rf"\b({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", s)
    if m:
        month = MONTHS.get(m.group(1))
        if month:
            return _build_date(today, month, int(m.group(2)))

    # "6 may" / "29th april"
    m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_ALT})\b", s)
    if m:
        month = MONTHS.get(m.group(2))
        if month:
            return _build_date(today, month, int(m.group(1)))

    return None


def extract_events(message: str, today: Optional[datetime] = None) -> dict:
    """
    Scan the user message for life events and return a structured dict.

    Returns
    -------
    dict with keys like "exam_period", "presentation", "interview", etc.
    Each value is a dict with date info and a "label" field.
    Empty dict if nothing detected.

    Examples
    --------
    "my exams are from today to may 6"
    -> {"exam_period": {"start": "2026-04-29", "end": "2026-05-06", "label": "exams", ...}}
    """
    if today is None:
        today = datetime.utcnow()

    events: dict = {}
    text = message.lower()

    # ── Exam period detection ────────────────────────────────────────────────
    has_exam_kw = any(kw in text for kw in EXAM_KEYWORDS)
    if has_exam_kw:
        # "from X to/till Y"
        m = re.search(
            r"\bfrom\s+(.+?)\s+(?:to|till|until)\s+(.+?)(?:[,\.!?]|$)", text
        )
        if m:
            start = _parse_date_str(m.group(1), today)
            end = _parse_date_str(m.group(2), today)
            if start or end:
                events["exam_period"] = {
                    "start": start or today.strftime("%Y-%m-%d"),
                    "end": end or start,
                    "label": "exams",
                    "detected_at": today.strftime("%Y-%m-%d"),
                }

        # "exams till/until X" (no explicit start)
        if "exam_period" not in events:
            m = re.search(r"\b(?:till|until|upto|up to)\s+(.+?)(?:[,\.!?]|$)", text)
            if m:
                end = _parse_date_str(m.group(1), today)
                if end:
                    events["exam_period"] = {
                        "start": today.strftime("%Y-%m-%d"),
                        "end": end,
                        "label": "exams",
                        "detected_at": today.strftime("%Y-%m-%d"),
                    }

    # ── Single exam day detection ("exam tomorrow", "exam today") ────────────
    if has_exam_kw and "exam_period" not in events:
        for phrase, delta in [("tomorrow", 1), ("today", 0), ("kal", 1), ("aaj", 0)]:
            if phrase in text:
                exam_date = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                events["exam_period"] = {
                    "start": exam_date,
                    "end": exam_date,
                    "label": "exam",
                    "detected_at": today.strftime("%Y-%m-%d"),
                }
                break

    # ── One-off event detection (presentation, interview, etc.) ─────────────
    for kw in EVENT_KEYWORDS:
        if kw in text:
            m = re.search(
                rf"\b{kw}\b.*?\b(?:on|by|at)?\s+(.+?)(?:[,\.!?]|$)", text
            )
            if m:
                ev_date = _parse_date_str(m.group(1).strip(), today)
                if ev_date:
                    events[kw] = {
                        "date": ev_date,
                        "label": kw,
                        "detected_at": today.strftime("%Y-%m-%d"),
                    }

    # ── Birthday detection ──────────────────────────────────────────────────
    has_bday_kw = any(kw in text for kw in BIRTHDAY_KEYWORDS)
    if has_bday_kw:
        # "birthday on may 6" / "bday tomorrow" / "birthday next week"
        bday_date = None

        # "birthday tomorrow / today"
        for phrase, delta in [("tomorrow", 1), ("today", 0), ("kal", 1), ("aaj", 0)]:
            if phrase in text:
                bday_date = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                break

        # "birthday on / in X days"
        if not bday_date:
            m = re.search(r"(?:in|after)\s+(\d+)\s+days?", text)
            if m:
                bday_date = (today + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

        # "birthday on <month day>"
        if not bday_date:
            m = re.search(
                rf"(?:on|is|was)?\s*(?:the)?\s*({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", text
            )
            if m:
                month = MONTHS.get(m.group(1))
                if month:
                    bday_date = _build_date(today, month, int(m.group(2)))

        if not bday_date:
            m = re.search(
                rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_ALT})\b", text
            )
            if m:
                month = MONTHS.get(m.group(2))
                if month:
                    bday_date = _build_date(today, month, int(m.group(1)))

        if bday_date:
            events["birthday"] = {
                "date": bday_date,
                "label": "birthday",
                "detected_at": today.strftime("%Y-%m-%d"),
            }

    return events


def get_proactive_context(life_events: dict, today: Optional[datetime] = None) -> Optional[str]:
    """
    Given stored life events from the user profile, return an LLM context hint
    if an event is active or upcoming. Returns None if nothing relevant today.

    This hint is injected into the system prompt so the bot can organically
    weave a friendly check-in into the conversation.
    """
    if not life_events:
        return None
    if today is None:
        today = datetime.utcnow()

    today_str = today.strftime("%Y-%m-%d")
    hints: list[str] = []

    # ── Exam period ──────────────────────────────────────────────────────────
    ep = life_events.get("exam_period")
    if ep:
        start = ep.get("start", "")
        end = ep.get("end", "")
        label = ep.get("label", "exams")

        if start and end:
            if start <= today_str <= end:
                hints.append(
                    f"[MEMORY] This student has {label} running from {start} to {end}. "
                    f"Today ({today_str}) is mid-exam period. If it feels natural, ask ONE casual "
                    f"question like 'Kal ka paper kaisa tha?' or 'Aaj kya hai?'. Keep it 1 short line."
                )
            elif today_str > end:
                try:
                    days_after = (today - datetime.strptime(end, "%Y-%m-%d")).days
                    if 0 < days_after <= 3:
                        hints.append(
                            f"[MEMORY] This student's {label} just ended on {end}. "
                            f"If it feels natural, ask how the exams went -- one short, encouraging line."
                        )
                except ValueError:
                    pass

    # ── One-off events ───────────────────────────────────────────────────────
    for kw in EVENT_KEYWORDS:
        ev = life_events.get(kw)
        if not ev:
            continue
        ev_date = ev.get("date", "")
        if not ev_date:
            continue
        if ev_date == today_str:
            hints.append(
                f"[MEMORY] The student has a {kw} today. If it feels natural, wish them luck casually."
            )
        else:
            try:
                days_until = (datetime.strptime(ev_date, "%Y-%m-%d") - today).days
                if 0 < days_until <= 2:
                    hints.append(
                        f"[MEMORY] The student has a {kw} in {days_until} day(s) on {ev_date}. "
                        f"If natural, mention it and ask if they feel ready."
                    )
            except ValueError:
                pass

    # ── Birthday ─────────────────────────────────────────────────────────────
    bday = life_events.get("birthday")
    if bday:
        bday_date = bday.get("date", "")
        if bday_date:
            if bday_date == today_str:
                hints.append(
                    "[MEMORY] TODAY IS THIS STUDENT'S BIRTHDAY! 🎂 "
                    "Open with a warm, heartfelt birthday wish — make them feel special. "
                    "Keep it genuine and fun, 1-2 lines max. Use 🎂🎉🎈 emojis."
                )
            else:
                try:
                    days_until = (datetime.strptime(bday_date, "%Y-%m-%d") - today).days
                    if days_until == 0:
                        pass  # Already handled above
                    elif 0 < days_until <= 3:
                        hints.append(
                            f"[MEMORY] The student's birthday is in {days_until} day(s) on {bday_date}. "
                            f"If natural, say something warm and exciting about their upcoming birthday — 1 short line."
                        )
                    elif days_until < 0 and abs(days_until) <= 1:
                        hints.append(
                            f"[MEMORY] The student's birthday was yesterday ({bday_date}). "
                            f"If natural, ask how they celebrated — 1 short warm line."
                        )
                except ValueError:
                    pass

    return "\n".join(hints) if hints else None
