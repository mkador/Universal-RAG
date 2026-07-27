"""
modules/utils.py
=================
Small shared utilities: logging setup, language detection (English / Bangla),
text cleaning, file helpers, and caching helpers.
"""

import hashlib
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from langdetect import detect, DetectorFactory, LangDetectException

from config import settings

# Make langdetect deterministic
DetectorFactory.seed = 0

_LOGGER_CACHE = {}


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
def get_logger(name: str = "universal_rag") -> logging.Logger:
    """Return a configured logger that writes to both console and a daily log file."""
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    _LOGGER_CACHE[name] = logger
    return logger


# ------------------------------------------------------------------
# Language detection (English / Bangla, with graceful fallback)
# ------------------------------------------------------------------
BANGLA_UNICODE_RANGE = re.compile(r"[\u0980-\u09FF]")


def detect_language(text: str) -> str:
    """
    Detect whether `text` is Bangla ('bn') or English ('en').
    Falls back to a Unicode-range heuristic if langdetect fails
    (e.g. very short strings) and defaults to English otherwise.
    """
    if not text or not text.strip():
        return "en"

    # Fast heuristic: if a meaningful share of characters are in the
    # Bangla Unicode block, treat it as Bangla immediately.
    bangla_chars = len(BANGLA_UNICODE_RANGE.findall(text))
    if bangla_chars > 0 and bangla_chars / max(len(text), 1) > 0.15:
        return "bn"

    try:
        code = detect(text)
        if code == "bn":
            return "bn"
        return "en"
    except LangDetectException:
        return "en"


def language_label(code: str) -> str:
    return {"en": "English", "bn": "Bangla (বাংলা)"}.get(code, "English")


# ------------------------------------------------------------------
# Text cleaning
# ------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Normalize whitespace while preserving Bangla/English content as-is."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------------
# File helpers
# ------------------------------------------------------------------
def allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.SUPPORTED_EXTENSIONS


def file_type_for(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return settings.SUPPORTED_EXTENSIONS.get(ext)


def save_uploaded_file(file_bytes: bytes, filename: str) -> Path:
    """
    Save an uploaded file into the correct data/<type>/ subfolder based on
    its extension, and also keep a copy in uploads/ for audit purposes.
    """
    file_type = file_type_for(filename)
    if file_type is None:
        raise ValueError(f"Unsupported file type: {filename}")

    target_dir = getattr(settings, f"{file_type.upper()}_DIR")
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(filename)
    target_path = target_dir / safe_name
    target_path.write_bytes(file_bytes)

    # audit copy
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (settings.UPLOADS_DIR / safe_name).write_bytes(file_bytes)

    # NOTE: আমরা এখানে logger ব্যবহার করছি না, কারণ এই ফাংশনটি যেকোনো জায়গা থেকে কল হতে পারে।
    # মূল অ্যাপে logger ব্যবহার করা হয়েছে।
    return target_path


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^\w\.\-\u0980-\u09FF ]", "_", name)
    return name


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()