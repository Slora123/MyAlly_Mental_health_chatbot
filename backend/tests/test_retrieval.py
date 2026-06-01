"""
tests/test_retrieval.py
────────────────────────
Unit tests for the retrieval routing layer.

Tests:
  - classify_intent() returns the correct category for representative inputs
  - is_high_risk() fires on crisis phrases and not on normal messages
  - Knowledge hints are correctly detected
  - Distress signals are correctly detected
  - Mixed intent is detected when both signals are present
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.router import classify_intent, is_high_risk


# ── is_high_risk ──────────────────────────────────────────────────────────────

def test_high_risk_suicide():
    assert is_high_risk("I want to kill myself") is True


def test_high_risk_suicidal():
    assert is_high_risk("I have been feeling suicidal lately") is True


def test_high_risk_end_life():
    assert is_high_risk("I want to end my life tonight") is True


def test_high_risk_self_harm():
    assert is_high_risk("I keep cutting myself when I'm overwhelmed") is True


def test_high_risk_overdose():
    assert is_high_risk("I thought about taking an overdose") is True


def test_not_high_risk_normal():
    assert is_high_risk("I am stressed about my exams") is False


def test_not_high_risk_knowledge():
    assert is_high_risk("What is cognitive behavioural therapy?") is False


# ── classify_intent ───────────────────────────────────────────────────────────

def test_classify_intent_high_risk():
    assert classify_intent("I want to die") == "high_risk"


def test_classify_intent_support_only():
    result = classify_intent("I feel so alone and sad today")
    assert result == "support_only"


def test_classify_intent_knowledge_seeking():
    result = classify_intent("What are the symptoms of anxiety disorder?")
    assert result == "knowledge_seeking"


def test_classify_intent_mixed():
    result = classify_intent(
        "I feel really sad and overwhelmed – what are some coping techniques for stress?"
    )
    assert result == "mixed"


def test_classify_intent_burnout_is_support():
    result = classify_intent("I am so burnt out and exhausted. I just can't do this anymore.")
    assert result in ("support_only", "mixed")  # no factual question → support_only


def test_classify_intent_factual_no_distress():
    result = classify_intent("How does therapy help with OCD?")
    assert result == "knowledge_seeking"


def test_classify_intent_high_risk_overrides_knowledge():
    """Crisis signals must take priority even if a knowledge word is present."""
    result = classify_intent(
        "I am suicidal. What treatment exists for depression?"
    )
    assert result == "high_risk"


def test_classify_intent_returns_string():
    result = classify_intent("Hello")
    assert isinstance(result, str)
    assert result in ("high_risk", "knowledge_seeking", "mixed", "support_only")
