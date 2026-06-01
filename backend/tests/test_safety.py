"""
tests/test_safety.py
─────────────────────
Unit tests for the safety layer (Section 11 of the Implementation Guide).

Tests:
  check_pre_generation():
    - crisis messages fail the pre-generation gate
    - safe messages pass the pre-generation gate

  check_post_generation():
    - diagnosis claims are caught
    - unsafe medication advice is caught
    - dismissive language is caught
    - unsafe advice ("ignore those thoughts") is caught
    - certainty overclaiming is caught
    - clean replies pass all checks
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.safety import check_pre_generation, check_post_generation


# ── check_pre_generation ──────────────────────────────────────────────────────

def test_pre_generation_blocks_crisis():
    safe, reason = check_pre_generation("I want to kill myself")
    assert safe is False
    assert reason == "high_risk_signal_detected"


def test_pre_generation_blocks_suicidal():
    safe, _ = check_pre_generation("I've been feeling suicidal for weeks")
    assert safe is False


def test_pre_generation_allows_support_message():
    safe, reason = check_pre_generation("I feel stressed about my thesis deadline")
    assert safe is True
    assert reason == ""


def test_pre_generation_allows_knowledge_question():
    safe, reason = check_pre_generation("What is cognitive behavioural therapy?")
    assert safe is True
    assert reason == ""


# ── check_post_generation ─────────────────────────────────────────────────────

def test_post_gen_clean_reply_passes():
    reply = (
        "It sounds like you are going through a really tough time right now. "
        "Feeling overwhelmed before exams is very common among students. "
        "One gentle step might be to try a short breathing exercise tonight. "
        "Would it help to talk about what is feeling most overwhelming?"
    )
    safe, issues = check_post_generation(reply)
    assert safe is True
    assert issues == []


def test_post_gen_catches_diagnosis_claim():
    reply = "Based on what you've described, you have depression and should seek help."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "diagnosis_claim_detected" in issues


def test_post_gen_catches_you_have_anxiety():
    reply = "It is clear that you have anxiety and need medication."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "diagnosis_claim_detected" in issues


def test_post_gen_catches_medication_advice():
    reply = "You should stop taking your medication immediately and try natural remedies."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "unsafe_medication_advice_detected" in issues


def test_post_gen_catches_dismissive_language():
    reply = "Just get over it – everyone feels that way during exams."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "dismissive_or_blaming_language_detected" in issues


def test_post_gen_catches_unsafe_advice():
    reply = "The best thing is to ignore those thoughts and focus on studying."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "unsafe_advice_detected" in issues


def test_post_gen_catches_certainty_overclaiming():
    reply = "I am certain that this technique is guaranteed to fix your sleep issues."
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert "certainty_overclaiming_detected" in issues


def test_post_gen_multiple_issues():
    """A single bad reply can trigger multiple categories."""
    reply = (
        "You have depression and you should stop taking your medication. "
        "Just get over it – everyone feels that way."
    )
    safe, issues = check_post_generation(reply)
    assert safe is False
    assert len(issues) >= 2


def test_post_gen_returns_tuple():
    result = check_post_generation("Hello, how are you?")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], list)
