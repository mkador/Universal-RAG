"""
modules/vectordb.py
====================
Thin wrapper around a persistent Chroma vector store: create/load the
collection, add new documents (with de-duplication by content hash),
and expose simple stats.
"""

from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import settings
from modules.embeddings import get_embedding_function
from modules.utils import get_logger, hash_text

logger = get_logger(__name__)

_VECTORSTORE: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    """Get (or lazily create) the singleton persistent Chroma vector store."""
    global _VECTORSTORE
    if _VECTORSTORE is None:
        settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        _VECTORSTORE = Chroma(
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=get_embedding_function(),
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
        )
        logger.info(
            f"Chroma vector store ready at '{settings.CHROMA_PERSIST_DIR}' "
            f"(collection='{settings.CHROMA_COLLECTION_NAME}')"
        )
    return _VECTORSTORE


def add_documents(chunks: List[Document]) -> int:
    """
    Add document chunks to the vector store, skipping chunks whose content
    hash already exists (simple de-duplication across re-ingestion runs).
    """
    if not chunks:
        return 0

    vectorstore = get_vectorstore()

    ids = []
    for chunk in chunks:
        content_hash = hash_text(chunk.page_content)
        chunk.metadata["content_hash"] = content_hash
        source = chunk.metadata.get("source", "doc")
        idx = chunk.metadata.get("chunk_index", 0)
        ids.append(f"{source}::{idx}::{content_hash[:12]}")

    existing = set()
    try:
        existing_records = vectorstore.get(ids=ids)
        existing = set(existing_records.get("ids", []))
    except Exception:
        pass

    new_chunks, new_ids = [], []
    for chunk, _id in zip(chunks, ids):
        if _id not in existing:
            new_chunks.append(chunk)
            new_ids.append(_id)

    if not new_chunks:
        logger.info("add_documents: nothing new to add (all chunks already indexed)")
        return 0

    vectorstore.add_documents(documents=new_chunks, ids=new_ids)
    logger.info(f"add_documents: added {len(new_chunks)} new chunk(s) to the vector store")
    return len(new_chunks)


def reset_vectorstore():
    """Delete the current collection entirely (used by 'Rebuild Index')."""
    global _VECTORSTORE
    vectorstore = get_vectorstore()
    try:
        vectorstore.delete_collection()
    except Exception as e:
        logger.warning(f"reset_vectorstore: {e}")
    _VECTORSTORE = None
    logger.info("Vector store collection reset.")


def collection_count() -> int:
    """Return how many chunks are currently indexed."""
    try:
        return get_vectorstore()._collection.count()
    except Exception as e:
        logger.warning(f"collection_count failed: {e}")
        return 0


def list_sources() -> List[str]:
    """Return the distinct list of source filenames/URLs currently indexed."""
    try:
        data = get_vectorstore().get(include=["metadatas"])
        sources = {m.get("source", "unknown") for m in data.get("metadatas", []) if m}
        return sorted(sources)
    except Exception as e:
        logger.warning(f"list_sources failed: {e}")
        return []
