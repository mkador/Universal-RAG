"""
modules/metadata.py
====================
Helpers for building consistent metadata during ingestion and for
formatting readable source citations to show under each answer.
"""

from datetime import datetime
from typing import List, Dict, Any

from langchain_core.documents import Document


def build_ingest_metadata(extra: Dict[str, Any] = None) -> Dict[str, Any]:
    """Common metadata stamped onto every document at ingestion time."""
    meta = {"ingested_at": datetime.utcnow().isoformat()}
    if extra:
        meta.update(extra)
    return meta


def format_citation(doc: Document) -> str:
    """Turn a retrieved chunk's metadata into a short, human-readable citation."""
    meta = doc.metadata or {}
    source = meta.get("source", "Unknown source")
    file_type = meta.get("file_type", "")

    if file_type == "pdf" and meta.get("page"):
        return f"{source} (p. {meta['page']})"
    if file_type == "excel" and meta.get("sheet"):
        return f"{source} — sheet '{meta['sheet']}'"
    if file_type == "website" and meta.get("url"):
        return f"{source} ({meta['url']})"
    return source


def format_sources(docs: List[Document]) -> List[str]:
    """De-duplicated, ordered list of citation strings for a set of retrieved chunks."""
    seen = []
    for doc in docs:
        c = format_citation(doc)
        if c not in seen:
            seen.append(c)
    return seen


def build_context_string(docs: List[Document]) -> str:
    """
    Concatenate retrieved chunks into a single context block for the LLM,
    each chunk labeled with its source so the model can cite it.
    """
    blocks = []
    for i, doc in enumerate(docs, start=1):
        citation = format_citation(doc)
        blocks.append(f"[Source {i}: {citation}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)
