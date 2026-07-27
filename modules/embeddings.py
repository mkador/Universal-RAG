"""
modules/embeddings.py
======================
Embedding function factory. Supports two providers:

- "openai"      -> OpenAI's text-embedding-3-large / small (excellent
                    multilingual quality, including Bangla), requires
                    OPENAI_API_KEY.
- "huggingface" -> sentence-transformers/paraphrase-multilingual-mpnet-base-v2
                    (runs locally, free, strong English + Bangla support).

The provider is chosen via EMBEDDING_PROVIDER in .env, with an automatic
fallback to HuggingFace if no OpenAI key is configured.
"""

from functools import lru_cache

from config import settings
from modules.utils import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embedding_function():
    """Return a LangChain-compatible embeddings object, cached for reuse."""
    provider = settings.EMBEDDING_PROVIDER

    if provider == "openai" and settings.OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings

        logger.info(f"Using OpenAI embeddings: {settings.OPENAI_EMBEDDING_MODEL}")
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    if provider == "openai" and not settings.OPENAI_API_KEY:
        logger.warning(
            "EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is missing. "
            "Falling back to local multilingual HuggingFace embeddings."
        )

    from langchain_huggingface import HuggingFaceEmbeddings

    logger.info(f"Using HuggingFace multilingual embeddings: {settings.HF_EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=settings.HF_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
