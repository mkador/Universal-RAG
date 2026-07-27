"""
config.py
==========
Central configuration for the Universal-RAG (English + Bangla) Business
Query System. All environment variables are loaded here so every other
module can simply `from config import settings`.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Load .env
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class Settings:
    # ---------------- Base paths ----------------
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    UPLOADS_DIR: Path = BASE_DIR / os.getenv("UPLOADS_DIR", "uploads")
    LOGS_DIR: Path = BASE_DIR / os.getenv("LOGS_DIR", "logs")
    CACHE_DIR: Path = BASE_DIR / os.getenv("CACHE_DIR", "cache")
    ASSETS_DIR: Path = BASE_DIR / "assets"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")

    # Sub-folders for each supported file type inside DATA_DIR
    PDF_DIR: Path = DATA_DIR / "pdf"
    DOCX_DIR: Path = DATA_DIR / "docx"
    EXCEL_DIR: Path = DATA_DIR / "excel"
    CSV_DIR: Path = DATA_DIR / "csv"
    TEXT_DIR: Path = DATA_DIR / "text"
    MARKDOWN_DIR: Path = DATA_DIR / "markdown"

    # ---------------- LLM ----------------
    # GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    # LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    LLM_TEMPERATURE: float = _get_float("LLM_TEMPERATURE", 0.2)

    # ---------------- Embeddings ----------------
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    HF_EMBEDDING_MODEL: str = os.getenv(
        "HF_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    )

    # ---------------- Vector DB ----------------
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "universal_rag_business")

    # ---------------- Chunking ----------------
    CHUNK_SIZE: int = _get_int("CHUNK_SIZE", 1000)
    CHUNK_OVERLAP: int = _get_int("CHUNK_OVERLAP", 150)

    # ---------------- Retrieval ----------------
    TOP_K: int = _get_int("TOP_K", 5)
    SEARCH_TYPE: str = os.getenv("SEARCH_TYPE", "mmr")  # "similarity" | "mmr"

    # ---------------- App ----------------
    APP_NAME: str = os.getenv("APP_NAME", "AI Universal RAG - Business Assistant")
    APP_LANGUAGES = tuple(os.getenv("APP_LANGUAGES", "en,bn").split(","))
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "auto")

    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".xlsx": "excel",
        ".xls": "excel",
        ".csv": "csv",
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
    }

    def ensure_directories(self):
        """Create all directories the app relies on if they don't exist."""
        for path in (
            self.DATA_DIR, self.UPLOADS_DIR, self.LOGS_DIR, self.CACHE_DIR,
            self.ASSETS_DIR, self.CHROMA_PERSIST_DIR,
            self.PDF_DIR, self.DOCX_DIR, self.EXCEL_DIR,
            self.CSV_DIR, self.TEXT_DIR, self.MARKDOWN_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
