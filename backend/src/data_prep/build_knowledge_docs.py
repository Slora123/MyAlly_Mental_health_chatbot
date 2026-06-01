"""
src/data_prep/build_knowledge_docs.py
──────────────────────────────────────
Section 6.5 of the Implementation Guide.

Processes:
  - mhqa-main/datasets/mhqa.csv   (gold set)
  - mhqa-main/datasets/mhqa-b.csv (silver set)

Applies:
  - valid_question filter when column is present
  - correct_answer / correct_option normalization
  - Drops rows missing question or answer
  - Unified document schema

Outputs:
  data/processed/knowledge_documents.jsonl
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3] / "database"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "knowledge_documents.jsonl"

_MHQA_FILES: dict[str, str] = {
    "mhqa_gold": "mhqa.csv",
    "mhqa_b":    "mhqa-b.csv",
}

def _get_path(filename: str, subfolder: str) -> Path | None:
    # Try subfolder first
    p1 = BASE_DIR / subfolder / filename
    if p1.exists(): return p1
    # Try root of database next
    p2 = BASE_DIR / filename
    if p2.exists(): return p2
    return None


def _normalise(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _get_correct_answer(row: dict) -> str:
    """
    Normalise correct_answer and correct_option into one output field.
    Section 6.5: 'normalize correct_answer and correct_option into one output field'.
    """
    return _normalise(row.get("correct_answer") or row.get("correct_option") or "")


def build_mhqa_documents() -> list[dict]:
    documents: list[dict] = []

    for subset, filename in _MHQA_FILES.items():
        path = _get_path(filename, "mhqa-main/datasets")
        if not path:
            print(f"  ⚠  {filename} not found in root or 'mhqa-main/datasets' – skipping.")
            continue

        df = pd.read_csv(path).fillna("")

        # Keep only valid rows if the validity flag column exists (Section 6.5)
        if "valid_question" in df.columns:
            df = df[df["valid_question"].apply(_is_true)]

        quality = 2 if subset == "mhqa_gold" else 1

        for index, row in df.iterrows():
            row_dict = row.to_dict()
            question = _normalise(row_dict.get("question", ""))
            correct_answer = _get_correct_answer(row_dict)
            topic = _normalise(row_dict.get("topic", "general")) or "general"
            question_type = _normalise(row_dict.get("type", "general")) or "general"

            # Drop rows missing core question or answer (Section 6.5)
            if not question or not correct_answer:
                continue

            options = [
                _normalise(row_dict.get("option1", "")),
                _normalise(row_dict.get("option2", "")),
                _normalise(row_dict.get("option3", "")),
                _normalise(row_dict.get("option4", "")),
            ]
            options_text = " | ".join(o for o in options if o)

            text = (
                f"Topic: {topic}\n"
                f"Question type: {question_type}\n"
                f"Question: {question}\n"
                f"Correct answer: {correct_answer}\n"
                f"Options: {options_text}"
            )
            documents.append(
                {
                    "id": f"{subset}-{index}",
                    "collection": "knowledge",
                    "text": text,
                    "metadata": {
                        "source": "mhqa",
                        "subset": subset,
                        "topic": topic,
                        "question_type": question_type,
                        "quality_score": quality,
                        "path": str(path.relative_to(BASE_DIR)),
                    },
                }
            )
    return documents


def build_all() -> list[dict]:
    print("  Building MHQA knowledge documents …")
    docs = build_mhqa_documents()
    print(f"    → {len(docs):,} MHQA documents")
    return docs


if __name__ == "__main__":
    from src.rag.index_builder import save_jsonl  # noqa: E402

    docs = build_all()
    save_jsonl(docs, OUTPUT_PATH)
    print(f"\nTotal knowledge documents: {len(docs):,}")
