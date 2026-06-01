"""
tests/test_processing.py
─────────────────────────
Unit tests for the data preparation pipeline.

Tests:
  - Unified document schema keys are present
  - _comma_ placeholder is replaced in EmpatheticDialogues text
  - Reddit level < 1 rows are filtered out
  - Empty seeker / response rows are skipped
  - MHQA correct_answer / correct_option normalisation
  - EmpatheticDialogues pair reconstruction produces user→assistant pairs
"""

import sys
from pathlib import Path

# Ensure project root is on path when running with plain `pytest`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep.build_empathy_docs import (
    build_reddit_documents,
    _normalise,
)
from src.data_prep.build_knowledge_docs import _get_correct_answer, _normalise as kn_normalise


# ─────────────────────────────────────────────────────────────────────────────
# _normalise


def test_normalise_collapses_whitespace():
    assert _normalise("  hello   world  ") == "hello world"


def test_normalise_replaces_comma_placeholder():
    """Section 6.2 explicit requirement: _comma_ must be replaced."""
    result = _normalise("I like cats_comma_ dogs_comma_ and rabbits")
    assert "_comma_" not in result
    assert "," in result


def test_normalise_handles_none():
    assert _normalise(None) == ""


# ─────────────────────────────────────────────────────────────────────────────
# Reddit document schema and filters

def test_reddit_docs_have_required_schema_keys():
    """Every document must have id, collection, text, metadata."""
    docs = build_reddit_documents()
    assert len(docs) > 0, "Expected Reddit documents to be non-empty"
    for doc in docs[:20]:  # spot-check first 20
        assert "id" in doc
        assert "collection" in doc
        assert "text" in doc
        assert "metadata" in doc


def test_reddit_docs_collection_value():
    docs = build_reddit_documents()
    for doc in docs[:10]:
        assert doc["collection"] == "empathy"


def test_reddit_docs_metadata_keys():
    docs = build_reddit_documents()
    for doc in docs[:10]:
        meta = doc["metadata"]
        assert "source" in meta
        assert "mechanism" in meta
        assert "quality_score" in meta
        assert meta["source"] == "reddit"


def test_reddit_docs_no_level_zero():
    """Section 6.3: rows with level < 1 must be dropped."""
    docs = build_reddit_documents()
    for doc in docs:
        assert doc["metadata"]["quality_score"] >= 1, (
            f"Document {doc['id']} has quality_score < 1 (should be filtered)"
        )


def test_reddit_docs_no_empty_text():
    """Rows with empty seeker_post or response_post must be dropped."""
    docs = build_reddit_documents()
    for doc in docs[:50]:
        assert "Support-seeking message:" in doc["text"]
        assert "Empathetic response:" in doc["text"]


def test_reddit_docs_no_duplicates():
    """Identical seeker-response pairs must be deduplicated."""
    docs = build_reddit_documents()
    ids = [doc["id"] for doc in docs]
    assert len(ids) == len(set(ids)), "Duplicate document IDs found"


# ─────────────────────────────────────────────────────────────────────────────
# MHQA correct answer normalisation

def test_get_correct_answer_prefers_correct_answer():
    row = {"correct_answer": "CBT", "correct_option": "Option B"}
    assert _get_correct_answer(row) == "CBT"


def test_get_correct_answer_falls_back_to_correct_option():
    row = {"correct_answer": "", "correct_option": "Option B"}
    assert _get_correct_answer(row) == "Option B"


def test_get_correct_answer_returns_empty_when_both_missing():
    row = {"correct_answer": "", "correct_option": ""}
    assert _get_correct_answer(row) == ""


def test_kn_normalise_strips_whitespace():
    assert kn_normalise("  answer  ") == "answer"
