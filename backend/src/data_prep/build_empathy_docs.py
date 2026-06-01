"""
src/data_prep/build_empathy_docs.py
─────────────────────────────────────
Sections 6.3 and 6.4 of the Implementation Guide.

Processes:
  - dataset reddit/  (emotional_reaction, interpretation, exploration)
  - empatheticdialogues/  (train, valid, test)

Applies:
  - _comma_ placeholder replacement (Section 6.2 explicit requirement)
  - level < 1 filter for Reddit rows
  - EmpatheticDialogues pair reconstruction (sort → group → pair)
  - Unified document schema

Outputs:
  data/processed/empathy_documents.jsonl
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3] / "database"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "empathy_documents.jsonl"


# ── Text helpers ──────────────────────────────────────────────────────────────

def _normalise(value: object) -> str:
    """Collapse whitespace and strip. Return empty string for None/NaN."""
    if value is None:
        return ""
    text = str(value)
    # Section 6.2: replace _comma_ placeholder
    text = text.replace("_comma_", ",")
    return " ".join(text.split())


# ── Reddit (Section 6.3) ──────────────────────────────────────────────────────

_REDDIT_MECHANISMS = {
    "emotional_reaction": "emotional-reactions-reddit.csv",
    "interpretation":     "interpretations-reddit.csv",
    "exploration":        "explorations-reddit.csv",
}

def _get_path(filename: str, subfolder: str) -> Path | None:
    # Try subfolder first
    p1 = BASE_DIR / subfolder / filename
    if p1.exists(): return p1
    # Try root of database next
    p2 = BASE_DIR / filename
    if p2.exists(): return p2
    return None


def build_reddit_documents() -> list[dict]:
    documents: list[dict] = []
    for mechanism, filename in _REDDIT_MECHANISMS.items():
        path = _get_path(filename, "dataset reddit")
        if not path:
            print(f"  ⚠  {filename} not found in root or 'dataset reddit' – skipping.")
            continue
            
        df = pd.read_csv(path).fillna("")
        df["level"] = pd.to_numeric(df["level"], errors="coerce").fillna(0).astype(int)

        seen: set[tuple[str, str]] = set()

        for index, row in df.iterrows():
            level = int(row["level"])
            # Drop level < 1 rows (Section 6.3 filter)
            if level < 1:
                continue

            seeker = _normalise(row["seeker_post"])
            response = _normalise(row["response_post"])
            rationales = _normalise(row.get("rationales", ""))

            # Drop empty rows
            if not seeker or not response:
                continue

            # Deduplicate identical seeker-response pairs (Section 6.3)
            pair = (seeker, response)
            if pair in seen:
                continue
            seen.add(pair)

            text = (
                f"Support-seeking message: {seeker}\n"
                f"Empathetic response: {response}\n"
                f"Empathy mechanism: {mechanism}\n"
                f"Empathy evidence: {rationales or 'not annotated'}"
            )
            documents.append(
                {
                    "id": f"reddit-{mechanism}-{index}",
                    "collection": "empathy",
                    "text": text,
                    "metadata": {
                        "source": "reddit",
                        "subset": "Empathy-Mental-Health",
                        "mechanism": mechanism,
                        "quality_score": level,
                        "path": str(path.relative_to(BASE_DIR)),
                    },
                }
            )
    return documents


# ── EmpatheticDialogues (Section 6.4) ─────────────────────────────────────────

def build_empathetic_dialogues_documents() -> list[dict]:
    documents: list[dict] = []
    dataset_dir = BASE_DIR / "empatheticdialogues"

    for split in ("train", "valid", "test"):
        filename = f"{split}.csv"
        path = _get_path(filename, "empatheticdialogues")
        if not path:
            print(f"  ⚠  {filename} not found in root or 'empatheticdialogues' – skipping.")
            continue

        df = pd.read_csv(path, on_bad_lines='skip').fillna("")
        df["utterance_idx"] = (
            pd.to_numeric(df["utterance_idx"], errors="coerce").fillna(0).astype(int)
        )

        # Sort → group → pair (Section 6.4)
        grouped = (
            df.sort_values(["conv_id", "utterance_idx"])
            .groupby("conv_id", sort=False)
        )

        for _, conversation in grouped:
            rows = conversation.to_dict("records")

            for pos in range(1, len(rows)):
                prev_row = rows[pos - 1]
                curr_row = rows[pos]

                # Only pair assistant turns (speaker_idx == 0)
                if str(curr_row.get("speaker_idx", "")).strip() != "0":
                    continue

                user_turn = _normalise(prev_row.get("utterance", ""))
                assistant_turn = _normalise(curr_row.get("utterance", ""))
                emotion = _normalise(
                    curr_row.get("context", "") or prev_row.get("context", "")
                )
                prompt_text = _normalise(
                    curr_row.get("prompt", "") or prev_row.get("prompt", "")
                )

                if not user_turn or not assistant_turn:
                    continue

                text = (
                    f"Emotion label: {emotion or 'unknown'}\n"
                    f"Situation prompt: {prompt_text or 'not provided'}\n"
                    f"Speaker message: {user_turn}\n"
                    f"Empathetic reply: {assistant_turn}"
                )
                doc_id = (
                    f"empatheticdialogues-{split}-"
                    f"{curr_row['conv_id']}-{curr_row['utterance_idx']}"
                )
                documents.append(
                    {
                        "id": doc_id,
                        "collection": "empathy",
                        "text": text,
                        "metadata": {
                            "source": "empatheticdialogues",
                            "emotion": emotion or "unknown",
                            "split": split,
                            "quality_score": 2,
                            "path": str(path.relative_to(BASE_DIR)),
                        },
                    }
                )
    return documents


# ── Main ──────────────────────────────────────────────────────────────────────

def build_all() -> list[dict]:
    """Build and return all empathy documents from both sources."""
    print("  Building Reddit empathy documents …")
    reddit_docs = build_reddit_documents()
    print(f"    → {len(reddit_docs):,} Reddit documents")

    print("  Building EmpatheticDialogues documents …")
    ed_docs = build_empathetic_dialogues_documents()
    print(f"    → {len(ed_docs):,} EmpatheticDialogues documents")

    return reddit_docs + ed_docs


if __name__ == "__main__":
    from src.rag.index_builder import save_jsonl   # noqa: E402

    docs = build_all()
    save_jsonl(docs, OUTPUT_PATH)
    print(f"\nTotal empathy documents: {len(docs):,}")
