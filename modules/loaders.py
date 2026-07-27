"""
modules/loaders.py
===================
Loads documents from every supported file type (PDF, DOCX, Excel, CSV,
plain text, Markdown) into a common list of LangChain `Document` objects,
each carrying rich metadata used later for citations.
"""

from pathlib import Path
from typing import List

import pandas as pd
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

from config import settings
from modules.utils import get_logger, clean_text, hash_file

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Individual loaders
# ------------------------------------------------------------------
def load_pdf(path: Path) -> List[Document]:
    """Load a PDF file, one Document per page, with page-number metadata."""
    docs = PyPDFLoader(str(path)).load()
    out = []
    for i, d in enumerate(docs):
        out.append(
            Document(
                page_content=clean_text(d.page_content),
                metadata={
                    "source": path.name,
                    "file_type": "pdf",
                    "page": d.metadata.get("page", i) + 1,
                    "path": str(path),
                },
            )
        )
    logger.info(f"Loaded PDF '{path.name}' -> {len(out)} page(s)")
    return out


def load_docx(path: Path) -> List[Document]:
    """Load a Word document as a single Document (split later by the splitter)."""
    docs = Docx2txtLoader(str(path)).load()
    out = [
        Document(
            page_content=clean_text(d.page_content),
            metadata={"source": path.name, "file_type": "docx", "path": str(path)},
        )
        for d in docs
    ]
    logger.info(f"Loaded DOCX '{path.name}'")
    return out


def load_excel(path: Path) -> List[Document]:
    """Load every sheet of an Excel workbook, one Document per sheet."""
    out = []
    try:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    except Exception as e:
        logger.error(f"Failed to read Excel file '{path.name}': {e}")
        return out

    for sheet_name, df in sheets.items():
        df = df.fillna("")
        text = df.to_markdown(index=False) if not df.empty else ""
        out.append(
            Document(
                page_content=clean_text(text),
                metadata={
                    "source": path.name,
                    "file_type": "excel",
                    "sheet": sheet_name,
                    "path": str(path),
                },
            )
        )
    logger.info(f"Loaded Excel '{path.name}' -> {len(out)} sheet(s)")
    return out


def load_csv(path: Path) -> List[Document]:
    """Load a CSV file as a single Markdown-table Document."""
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception as e:
        logger.error(f"Failed to read CSV file '{path.name}': {e}")
        return []

    text = df.to_markdown(index=False) if not df.empty else ""
    doc = Document(
        page_content=clean_text(text),
        metadata={"source": path.name, "file_type": "csv", "path": str(path)},
    )
    logger.info(f"Loaded CSV '{path.name}' -> {len(df)} row(s)")
    return [doc]


def load_text(path: Path) -> List[Document]:
    docs = TextLoader(str(path), encoding="utf-8").load()
    out = [
        Document(
            page_content=clean_text(d.page_content),
            metadata={"source": path.name, "file_type": "text", "path": str(path)},
        )
        for d in docs
    ]
    logger.info(f"Loaded text file '{path.name}'")
    return out


def load_markdown(path: Path) -> List[Document]:
    try:
        docs = UnstructuredMarkdownLoader(str(path)).load()
    except Exception as e:
        logger.warning(f"Unstructured markdown loader failed for '{path.name}', falling back to plain text: {e}")
        docs = TextLoader(str(path), encoding="utf-8").load()

    out = [
        Document(
            page_content=clean_text(d.page_content),
            metadata={"source": path.name, "file_type": "markdown", "path": str(path)},
        )
        for d in docs
    ]
    logger.info(f"Loaded Markdown file '{path.name}'")
    return out


# ------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------
_LOADER_MAP = {
    "pdf": load_pdf,
    "docx": load_docx,
    "excel": load_excel,
    "csv": load_csv,
    "text": load_text,
    "markdown": load_markdown,
}


def load_file(path: Path) -> List[Document]:
    """Load a single file, dispatching on its extension."""
    ext = path.suffix.lower()
    file_type = settings.SUPPORTED_EXTENSIONS.get(ext)
    if file_type is None:
        logger.warning(f"Skipping unsupported file: {path.name}")
        return []

    loader_fn = _LOADER_MAP[file_type]
    try:
        docs = loader_fn(path)
        for d in docs:
            d.metadata["file_hash"] = hash_file(path)
        return docs
    except Exception as e:
        logger.error(f"Failed to load '{path.name}': {e}")
        return []


def load_directory(base_dir: Path = None) -> List[Document]:
    """
    Walk data/pdf, data/docx, data/excel, data/csv, data/text, data/markdown
    (or a custom base_dir with the same layout) and load every supported
    file found into a single flat list of Documents.
    """
    base_dir = base_dir or settings.DATA_DIR
    all_docs: List[Document] = []

    sub_dirs = {
        "pdf": settings.PDF_DIR,
        "docx": settings.DOCX_DIR,
        "excel": settings.EXCEL_DIR,
        "csv": settings.CSV_DIR,
        "text": settings.TEXT_DIR,
        "markdown": settings.MARKDOWN_DIR,
    }

    for file_type, folder in sub_dirs.items():
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and not path.name.startswith("."):
                all_docs.extend(load_file(path))

    logger.info(f"load_directory: loaded {len(all_docs)} document chunks total from {base_dir}")
    return all_docs
