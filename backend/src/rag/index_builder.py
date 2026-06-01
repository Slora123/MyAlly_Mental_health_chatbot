"""
src/rag/index_builder.py
─────────────────────────
Section 8 of the Implementation Guide: Embeddings and Vector Indexing.

Handles:
  - rebuild_collection()   : delete + recreate a named Chroma collection
  - upsert_documents()     : batch upsert from a list of document dicts
  - load_jsonl()           : load processed JSONL records into memory
  - save_jsonl()           : save document dicts to a JSONL file

These utilities are shared between build_rag_index.py (offline) and tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import chromadb

BATCH_SIZE = 20


def rebuild_collection(
    chroma_client: chromadb.ClientAPI,
    collection_name: str,
    embedding_function,
    skip_if_populated: bool = False
) -> chromadb.Collection:
    """
    Delete a collection if it exists and recreate it.
    If skip_if_populated is True, it will return the existing collection
    if it already has documents, avoiding a full re-index.
    """
    if skip_if_populated:
        try:
            col = chroma_client.get_collection(name=collection_name, embedding_function=embedding_function)
            if col.count() > 0:
                print(f"  ✨ Collection '{collection_name}' already populated ({col.count()} docs). Skipping rebuild.")
                return col
        except Exception:
            pass

    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass
        
    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )


def batch_items(items: list, batch_size: int = BATCH_SIZE):
    """Yield successive slices of `items` of size `batch_size`."""
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def upsert_documents(
    collection: chromadb.Collection,
    items: list[dict],
) -> None:
    """
    Batch-upsert document dicts into a Chroma collection.
    Includes retry logic for Hugging Face API rate limits.
    """
    import time
    for batch in batch_items(items, BATCH_SIZE):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                collection.upsert(
                    ids=[item["id"] for item in batch],
                    documents=[item["document"] for item in batch],
                    metadatas=[item["metadata"] for item in batch],
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to upsert batch after {max_retries} attempts. Error: {e}")
                    raise
                sleep_time = (2 ** attempt) * 2
                print(f"  [Rate Limit/Error] Retrying in {sleep_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(sleep_time)


def save_jsonl(records: list[dict], path: Path) -> None:
    """Persist a list of document dicts to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    print(f"  Saved {len(records):,} records → {path}")


def load_jsonl(path: Path) -> list[dict]:
    """Load document dicts from a JSONL file."""
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
