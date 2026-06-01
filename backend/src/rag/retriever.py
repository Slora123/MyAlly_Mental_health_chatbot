"""
src/rag/retriever.py
─────────────────────
Section 9 of the Implementation Guide: Retrieval Strategy.

Handles:
  - Step 9.2  empathy retrieval (top-k=6 → rerank → top 3)
  - Step 9.3  knowledge retrieval (top-k=3, conditional)
  - Step 9.4  simple reranking by quality_score + distance + source diversity
  - Step 9.5  context rendering (empathy and knowledge kept separate)
"""

from __future__ import annotations

import chromadb


# ── Low-level collection query ────────────────────────────────────────────────

def query_collection(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int,
) -> list[dict]:
    """
    Query a Chroma collection and return a flat list of result dicts.

    Each dict has keys: id, document, metadata, distance.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    return [
        {
            "id": item_id,
            "document": doc,
            "metadata": meta or {},
            "distance": dist,
        }
        for item_id, doc, meta, dist in zip(ids, documents, metadatas, distances)
    ]


# ── Reranking (Step 9.4) ──────────────────────────────────────────────────────

def _rerank_empathy(candidates: list[dict], top_n: int = 3) -> list[dict]:
    """
    Rerank empathy candidates by:
      1. Higher quality_score (descending)
      2. Lower semantic distance (ascending)
      3. Source diversity: prefer items from different sources
    """
    # Sort by quality descending, then distance ascending
    candidates.sort(
        key=lambda item: (
            -int(item["metadata"].get("quality_score", 0)),
            item["distance"],
        )
    )

    # Source diversity: keep at most 2 items from the same source
    selected: list[dict] = []
    source_counts: dict[str, int] = {}
    for item in candidates:
        src = item["metadata"].get("source", "unknown")
        if source_counts.get(src, 0) < 2:
            selected.append(item)
            source_counts[src] = source_counts.get(src, 0) + 1
        if len(selected) >= top_n:
            break

    # Pad if diversity filter was too strict
    if len(selected) < top_n:
        for item in candidates:
            if item not in selected:
                selected.append(item)
            if len(selected) >= top_n:
                break

    return selected[:top_n]


# ── Public retrieval API ──────────────────────────────────────────────────────

def retrieve_empathy_examples(
    collection: chromadb.Collection,
    user_message: str,
    top_n: int = 3
) -> list[dict]:
    """
    Query the empathy collection with top-k=6, then rerank to top_n.
    Always called for support-only and mixed messages.
    """
    candidates = query_collection(collection, user_message, n_results=6)
    return _rerank_empathy(candidates, top_n=top_n)


def retrieve_knowledge_snippets(
    collection: chromadb.Collection,
    user_message: str,
) -> list[dict]:
    """
    Query the knowledge collection with top-k=3.
    Only called for knowledge-seeking and mixed messages.
    """
    return query_collection(collection, user_message, n_results=3)


# ── Context rendering (Step 9.5) ──────────────────────────────────────────────

def _normalise_text(value: object, limit: int = 260) -> str:
    text = " ".join(str(value).split()) if value is not None else ""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def render_empathy_context(items: list[dict]) -> str:
    """Render empathy examples as a labelled, numbered block for the prompt."""
    if not items:
        return "No empathy examples found."
    lines = []
    for i, item in enumerate(items, start=1):
        meta = item["metadata"]
        label = meta.get("source", "unknown")
        mechanism = meta.get("mechanism") or meta.get("emotion") or "general"
        lines.append(
            f"{i}. [{label} | {mechanism}] {_normalise_text(item['document'])}"
        )
    return "\n".join(lines)


def render_knowledge_context(items: list[dict]) -> str:
    """Render knowledge snippets as a labelled, numbered block for the prompt."""
    if not items:
        return "No mental-health knowledge snippets found."
    lines = []
    for i, item in enumerate(items, start=1):
        meta = item["metadata"]
        topic = meta.get("topic", "general")
        qtype = meta.get("question_type", "general")
        lines.append(f"{i}. [{topic} | {qtype}] {_normalise_text(item['document'])}")
    return "\n".join(lines)
