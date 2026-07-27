"""
modules/splitter.py
====================
Splits raw Documents into retrieval-sized chunks. Uses a separator list
that works well for both English and Bangla text (Bangla uses the same
punctuation marks '।' as a full-stop equivalent, which is included).
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from modules.utils import get_logger

logger = get_logger(__name__)

# Separators ordered from "biggest break" to "smallest break".
# '\u0964' == '।' the Bangla / Devanagari sentence-ending danda.
BILINGUAL_SEPARATORS = [
    "\n\n",
    "\n",
    "।",
    "\u0964",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
    "",
]


def get_text_splitter(chunk_size: int = None, chunk_overlap: int = None) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
        separators=BILINGUAL_SEPARATORS,
        length_function=len,
    )


def split_documents(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """Split a list of Documents into smaller chunks, preserving metadata
    and adding a `chunk_index` field so citations can reference exact chunks."""
    if not documents:
        return []

    splitter = get_text_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(documents)

    # Add a stable per-source chunk index for nicer citations
    counters = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        counters[source] = counters.get(source, 0) + 1
        chunk.metadata["chunk_index"] = counters[source]

    logger.info(f"split_documents: {len(documents)} docs -> {len(chunks)} chunks")
    return chunks
