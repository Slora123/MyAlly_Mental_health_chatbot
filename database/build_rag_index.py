"""
build_rag_index.py
───────────────────
Offline index builder.  Run once (or whenever the processing rules change)
to populate the two Chroma collections used by the app.

Changes from the original flat implementation:
  1. _comma_ placeholder replacement is now applied (Section 6.2)
  2. Processed documents are saved to data/processed/*.jsonl (Phase 2)
  3. Embedding and collection logic delegated to src/rag/ modules
  4. Build version is printed on completion for traceability (Section 8)

Usage:
    python build_rag_index.py
"""

import datetime
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR.parent / "backend"))

import chromadb

from src.data_prep.build_empathy_docs import build_all as build_empathy_docs
from src.data_prep.build_knowledge_docs import build_all as build_knowledge_docs
from src.rag.embeddings import get_embedding_function
from src.rag.index_builder import rebuild_collection, save_jsonl, upsert_documents

DB_PATH = BASE_DIR / "chroma_db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
EMPATHY_COLLECTION_NAME = "student_support_empathy"
KNOWLEDGE_COLLECTION_NAME = "student_support_knowledge"
BUILD_VERSION = "2.0"


def main() -> None:
    build_start = datetime.datetime.now()
    print("=" * 64)
    print(f"  MyAlly – RAG Index Builder  (version {BUILD_VERSION})")
    print(f"  Started : {build_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 64)

    # ── Step 3: Embed and index into Chroma ───────────────────────────────────
    print("\n[3/4] Indexing into Chroma …")
    chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
    embedding_function = get_embedding_function()
    
    import os
    force_reindex = os.getenv("FORCE_REINDEX", "false").lower() == "true"
    skip_if_populated = not force_reindex

    empathy_collection = rebuild_collection(
        chroma_client, EMPATHY_COLLECTION_NAME, embedding_function,
        skip_if_populated=skip_if_populated
    )
    knowledge_collection = rebuild_collection(
        chroma_client, KNOWLEDGE_COLLECTION_NAME, embedding_function,
        skip_if_populated=skip_if_populated
    )

    # Check if we can skip the expensive build steps
    if skip_if_populated and empathy_collection.count() > 0 and knowledge_collection.count() > 0:
        print("\n  ✅ Collections are already populated. Skipping heavy data processing.")
    else:
        # ── Step 1 & 2: Build or Load processed document lists ────────────────────
        empathy_jsonl = PROCESSED_DIR / "empathy_documents.jsonl"
        knowledge_jsonl = PROCESSED_DIR / "knowledge_documents.jsonl"
        
        from src.rag.index_builder import load_jsonl

        if empathy_jsonl.exists() and knowledge_jsonl.exists():
            print("\n[1/4] Loading pre-processed JSONL records …")
            empathy_docs = load_jsonl(empathy_jsonl)
            knowledge_docs = load_jsonl(knowledge_jsonl)
        else:
            print("\n[1/4] Building empathy documents from CSVs …")
            empathy_docs = build_empathy_docs()
            print("\n[2/4] Building knowledge documents from CSVs …")
            knowledge_docs = build_knowledge_docs()
            
            print("\n[2.5/4] Saving processed JSONL records …")
            save_jsonl(empathy_docs, empathy_jsonl)
            save_jsonl(knowledge_docs, knowledge_jsonl)

        # Chroma expects `document` key (not `text`) for the documents list
        def _to_chroma(docs: list[dict]) -> list[dict]:
            return [
                {**d, "document": d["text"]}
                for d in docs
            ]

        print("\n[4/4] Upserting documents …")
        upsert_documents(empathy_collection, _to_chroma(empathy_docs))
        upsert_documents(knowledge_collection, _to_chroma(knowledge_docs))

    # ── Summary ───────────────────────────────────────────────────────────────
    build_end = datetime.datetime.now()
    elapsed = (build_end - build_start).total_seconds()

    print("\n" + "=" * 64)
    print(f"  Build complete in {elapsed:.1f}s")
    if 'empathy_docs' in locals():
        print(f"  Empathy documents  : {len(empathy_docs):,}")
        print(f"  Knowledge documents: {len(knowledge_docs):,}")
    else:
        print(f"  Empathy documents  : {empathy_collection.count():,} (existing)")
        print(f"  Knowledge documents: {knowledge_collection.count():,} (existing)")
    print(f"  Chroma DB path     : {DB_PATH}")
    print(f"  JSONL output dir   : {PROCESSED_DIR}")
    print(f"  Build version      : {BUILD_VERSION}")
    print(f"  Finished at        : {build_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 64)


if __name__ == "__main__":
    main()
