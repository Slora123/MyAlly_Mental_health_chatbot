"""
src/data_prep/profile_data.py
─────────────────────────────
Section 6.1 of the Implementation Guide: Audit each CSV before transforming.

Run with:
    python src/data_prep/profile_data.py

Prints a structured profile for every dataset CSV so that you can write
correct filters and catch data-quality issues before building the index.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

# ── Dataset manifest ──────────────────────────────────────────────────────────
DATASETS = [
    {
        "name": "Reddit – Emotional Reactions",
        "path": BASE_DIR / "dataset reddit" / "emotional-reactions-reddit.csv",
        "text_cols": ["seeker_post", "response_post"],
        "label_col": "level",
    },
    {
        "name": "Reddit – Interpretations",
        "path": BASE_DIR / "dataset reddit" / "interpretations-reddit.csv",
        "text_cols": ["seeker_post", "response_post"],
        "label_col": "level",
    },
    {
        "name": "Reddit – Explorations",
        "path": BASE_DIR / "dataset reddit" / "explorations-reddit.csv",
        "text_cols": ["seeker_post", "response_post"],
        "label_col": "level",
    },
    {
        "name": "EmpatheticDialogues – train",
        "path": BASE_DIR / "empatheticdialogues" / "train.csv",
        "text_cols": ["utterance"],
        "label_col": "context",
    },
    {
        "name": "EmpatheticDialogues – valid",
        "path": BASE_DIR / "empatheticdialogues" / "valid.csv",
        "text_cols": ["utterance"],
        "label_col": "context",
    },
    {
        "name": "EmpatheticDialogues – test",
        "path": BASE_DIR / "empatheticdialogues" / "test.csv",
        "text_cols": ["utterance"],
        "label_col": "context",
    },
    {
        "name": "MHQA – mhqa.csv",
        "path": BASE_DIR / "mhqa-main" / "datasets" / "mhqa.csv",
        "text_cols": ["question"],
        "label_col": "topic",
    },
    {
        "name": "MHQA – mhqa-b.csv",
        "path": BASE_DIR / "mhqa-main" / "datasets" / "mhqa-b.csv",
        "text_cols": ["question"],
        "label_col": "topic",
    },
]


def _avg_text_length(df: pd.DataFrame, cols: list) -> dict:
    """Return average character length for each text column that exists."""
    result = {}
    for col in cols:
        if col in df.columns:
            result[col] = df[col].dropna().astype(str).str.len().mean()
    return result


def _label_distribution(df: pd.DataFrame, col: Optional[str]) -> dict:
    """Return value_counts for a label column, limited to top 10 values."""
    if not col or col not in df.columns:
        return {}
    vc = df[col].value_counts(dropna=False)
    return vc.head(10).to_dict()


def _check_comma_placeholder(df: pd.DataFrame, cols: list) -> bool:
    """Detect whether any text column contains the _comma_ placeholder."""
    for col in cols:
        if col in df.columns:
            if df[col].astype(str).str.contains("_comma_", na=False).any():
                return True
    return False


def profile_dataset(entry: dict) -> None:  # noqa: E731
    path: Path = entry["path"]
    name: str = entry["name"]
    text_cols: list[str] = entry["text_cols"]
    label_col: Optional[str] = entry.get("label_col")

    sep = "─" * 68
    print(f"\n{sep}")
    print(f"  {name}")
    print(f"  File : {path}")
    print(sep)

    if not path.exists():
        print("  ⚠  FILE NOT FOUND – skipping.\n")
        return

    df = pd.read_csv(path, low_memory=False, on_bad_lines="skip")

    print(f"  Rows       : {len(df):,}")
    print(f"  Columns    : {list(df.columns)}")
    print(f"  Duplicates : {int(df.duplicated().sum()):,}")

    print("\n  Null counts per column:")
    null_counts = df.isna().sum()
    for col, n in null_counts.items():
        if n > 0:
            print(f"    {col:40s} {n:,}")
    if null_counts.sum() == 0:
        print("    (none)")

    avg_lens = _avg_text_length(df, text_cols)
    if avg_lens:
        print("\n  Average text length (chars):")
        for col, avg in avg_lens.items():
            print(f"    {col:40s} {avg:.1f}")

    dist = _label_distribution(df, label_col)
    if dist:
        print(f"\n  Label distribution – '{label_col}' (top 10):")
        for label, count in dist.items():
            print(f"    {str(label):30s} {count:,}")

    has_comma = _check_comma_placeholder(df, text_cols)
    if has_comma:
        print("\n  ⚠  Contains '_comma_' placeholder – must be replaced before indexing.")

    # EmpatheticDialogues specific: check level=0 rows if column exists
    if "level" in df.columns:
        level_zero = (pd.to_numeric(df["level"], errors="coerce").fillna(0) < 1).sum()
        print(f"\n  Rows with level < 1 (to drop): {int(level_zero):,}")


def main() -> None:
    print("=" * 68)
    print("  MyAlly – Dataset Profiling Report")
    print("  Section 6.1 of the Implementation Guide")
    print("=" * 68)

    for entry in DATASETS:
        profile_dataset(entry)

    print("\n" + "=" * 68)
    print("  Profiling complete.")
    print("=" * 68)


if __name__ == "__main__":
    main()
