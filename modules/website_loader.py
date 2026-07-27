"""
modules/website_loader.py
==========================
Fetches a web page and extracts clean, readable text (supports Bangla
and English pages) as a LangChain Document, so business users can add
their own website / blog / policy pages as a knowledge source.
"""

from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

from modules.utils import get_logger, clean_text

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UniversalRAGBot/1.0; "
        "+https://example.com/bot) Business-RAG-Ingestor"
    )
}

# Tags whose content is noise, not article content
_STRIP_TAGS = ["script", "style", "nav", "footer", "header", "form", "noscript", "svg", "aside"]


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def load_website(url: str, timeout: int = 15) -> List[Document]:
    """
    Fetch `url`, strip boilerplate (nav/footer/scripts), and return a single
    Document with the readable page text plus metadata (url, title, domain).
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch website '{url}': {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = _extract_title(soup)

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n") if main else soup.get_text(separator="\n")
    text = clean_text(text)

    if not text:
        logger.warning(f"No readable text extracted from '{url}'")
        return []

    domain = urlparse(url).netloc

    doc = Document(
        page_content=text,
        metadata={
            "source": title or domain,
            "file_type": "website",
            "url": url,
            "domain": domain,
        },
    )
    logger.info(f"Loaded website '{url}' -> {len(text)} characters")
    return [doc]


def load_websites(urls: List[str]) -> List[Document]:
    """Load multiple URLs, skipping any that fail."""
    docs: List[Document] = []
    for url in urls:
        docs.extend(load_website(url))
    return docs
