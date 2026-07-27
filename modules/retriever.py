"""
modules/retriever.py
=====================
Builds a LangChain retriever on top of the Chroma vector store, supporting
plain similarity search or MMR (Maximal Marginal Relevance) for more
diverse, less redundant business answers.
"""

from typing import Optional

from config import settings
from modules.vectordb import get_vectorstore
from modules.utils import get_logger

logger = get_logger(__name__)


def get_retriever(
    top_k: Optional[int] = None,
    search_type: Optional[str] = None,
    source_filter: Optional[str] = None,
):
    """
    Return a retriever.

    Args:
        top_k: number of chunks to retrieve (default: settings.TOP_K)
        search_type: "similarity" or "mmr" (default: settings.SEARCH_TYPE)
        source_filter: optionally restrict retrieval to a single source
                       filename (useful for "ask this document only" mode)
    """
    vectorstore = get_vectorstore()
    k = top_k or settings.TOP_K
    stype = (search_type or settings.SEARCH_TYPE).lower()

    search_kwargs = {"k": k}
    if stype == "mmr":
        search_kwargs.update({"fetch_k": max(k * 4, 20), "lambda_mult": 0.5})
    if source_filter:
        search_kwargs["filter"] = {"source": source_filter}

    logger.info(f"Building retriever: type={stype}, k={k}, filter={source_filter}")
    return vectorstore.as_retriever(search_type=stype, search_kwargs=search_kwargs)
