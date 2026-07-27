# """
# modules/website_loader.py
# ==========================
# Fetches a web page and extracts clean, readable text (supports Bangla
# and English pages) as a LangChain Document, so business users can add
# their own website / blog / policy pages as a knowledge source.
# """

# from typing import List, Optional
# from urllib.parse import urlparse

# import requests
# from bs4 import BeautifulSoup
# from langchain_community.documents_loaders import WebBaseLoader

# from modules.utils import get_logger, clean_text

# logger = get_logger(__name__)

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (compatible; UniversalRAGBot/1.0; "
#         "+https://example.com/bot) Business-RAG-Ingestor"
#     )
# }

# # Tags whose content is noise, not article content
# _STRIP_TAGS = ["script", "style", "nav", "footer", "header", "form", "noscript", "svg", "aside"]


# def _extract_title(soup: BeautifulSoup) -> str:
#     if soup.title and soup.title.string:
#         return soup.title.string.strip()
#     h1 = soup.find("h1")
#     return h1.get_text(strip=True) if h1 else ""


# def load_website(url: str, timeout: int = 15) -> List[Document]:
#     """
#     Fetch `url`, strip boilerplate (nav/footer/scripts), and return a single
#     Document with the readable page text plus metadata (url, title, domain).
#     """
#     try:
#         resp = requests.get(url, headers=HEADERS, timeout=timeout)
#         resp.raise_for_status()
#     except requests.RequestException as e:
#         logger.error(f"Failed to fetch website '{url}': {e}")
#         return []

#     soup = BeautifulSoup(resp.text, "lxml")

#     for tag_name in _STRIP_TAGS:
#         for tag in soup.find_all(tag_name):
#             tag.decompose()

#     title = _extract_title(soup)

#     main = soup.find("main") or soup.find("article") or soup.body or soup
#     text = main.get_text(separator="\n") if main else soup.get_text(separator="\n")
#     text = clean_text(text)

#     if not text:
#         logger.warning(f"No readable text extracted from '{url}'")
#         return []

#     domain = urlparse(url).netloc

#     doc = Document(
#         page_content=text,
#         metadata={
#             "source": title or domain,
#             "file_type": "website",
#             "url": url,
#             "domain": domain,
#         },
#     )
#     logger.info(f"Loaded website '{url}' -> {len(text)} characters")
#     return [doc]


# def load_websites(urls: List[str]) -> List[Document]:
#     """Load multiple URLs, skipping any that fail."""
#     docs: List[Document] = []
#     for url in urls:
#         docs.extend(load_website(url))
#     return docs

"""
modules/website_loader.py
=========================

Production-ready Website Loader for Universal-RAG

Pipeline:
1. Playwright (JavaScript - Primary using async/await for Windows compatibility)
2. Trafilatura (Static HTML - Fallback 1)
3. BeautifulSoup (Static HTML - Fallback 2)
"""

import asyncio
import sys
from typing import List
from urllib.parse import urlparse

import requests
import trafilatura

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright  # 🔥 async version ব্যবহার করছি

from langchain_core.documents import Document

from modules.utils import get_logger, clean_text

logger = get_logger(__name__)

# আধুনিক ব্রাউজারের মতো ইউজার-এজেন্ট
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/120.0.0.0 Safari/537.36"
        " Edg/120.0.0.0"
    )
}

# বাদ দিতে হবে এমন ট্যাগ
REMOVE_TAGS = [
    "script", "style", "nav", "header", "footer", "aside",
    "noscript", "svg", "form", "iframe", "button", "input"
]

session = requests.Session()
session.headers.update(HEADERS)


class WebsiteLoader:

    def __init__(self, timeout: int = 45):
        self.timeout = timeout

    def _metadata(self, url: str, title: str, method: str):
        return {
            "source": url,
            "url": url,
            "title": title,
            "domain": urlparse(url).netloc,
            "file_type": "website",
            "loader": "website_loader",
            "extraction_method": method,
        }

    # ------------------------------------------------------------------
    # 🔥 Playwright - Async সংস্করণ (Windows-এর NotImplementedError সমাধান)
    # ------------------------------------------------------------------
    async def _async_fetch_html(self, url: str) -> str | None:
        """Playwright দিয়ে HTML ডাউনলোড করার অ্যাসিঙ্ক ফাংশন"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": 1920, "height": 1080},
                user_agent=HEADERS["User-Agent"]
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            
            # লেজি লোডিংয়ের জন্য অপেক্ষা
            await page.wait_for_timeout(8000)
            
            html = await page.content()
            await browser.close()
            return html

    def _extract_playwright(self, url: str):
        """সিঙ্ক্রোনাস মেথড যা অ্যাসিঙ্ক ফাংশনকে কল করে"""
        try:
            # Windows-এ Proactor Policy জোর করে সেট করা
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

            # async ফাংশনটি রান করা (এটি একটি নতুন লুপ তৈরি করবে)
            html = asyncio.run(self._async_fetch_html(url))
            
            if not html:
                return None

            # BeautifulSoup দিয়ে পার্স করুন
            soup = BeautifulSoup(html, "lxml")

            # অপ্রয়োজনীয় ট্যাগ বাদ দিন
            for tag in REMOVE_TAGS:
                for t in soup.find_all(tag):
                    t.decompose()

            # টাইটেল বের করুন
            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            # 🎯 স্পেসিফিক সাইটের জন্য কাস্টম সিলেক্টর
            target_selectors = [
                # জেনেরিক
                "main", "article", ".content", ".container", ".site-main",
                # WordPress
                ".entry-content", ".post-content", ".single-content",
                # Next.js / React
                "#__next", ".content-wrapper",
                # 🆕 Rokomari (বইয়ের ডিটেইল)
                "#book-detail", ".book-info", ".book-details", "#product-detail",
                # 🆕 Olympic BD / ই-কমার্স
                ".product-description", ".detail-info", ".product-details",
                # শেষ ভরসা (পুরো বডি)
                "body"
            ]

            main_content = None
            extracted_text = ""

            # প্রতিটি সিলেক্টর চেক করে সবচেয়ে বড় টেক্সট যেখানে আছে সেটা নিন
            for selector in target_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text("\n", strip=True)
                    if len(text) > len(extracted_text):
                        extracted_text = text
                        main_content = element
                        if len(extracted_text) > 1000:
                            break

            # যদি কোনো সিলেক্টরই কাজ না করে, পুরো soup থেকে নিন
            if not main_content or len(extracted_text) < 50:
                main_content = soup
                extracted_text = soup.get_text("\n", strip=True)

            final_text = clean_text(extracted_text)

            if not final_text or len(final_text) < 50:
                logger.warning(f"Playwright: খুব কম টেক্সট পেয়েছে ({len(final_text)} chars).")
                with open("debug_playwright_fail.html", "w", encoding="utf-8") as f:
                    f.write(html)
                return None

            logger.info("Playwright extraction successful.")
            return Document(
                page_content=final_text,
                metadata=self._metadata(url, title, "playwright"),
            )

        except Exception as e:
            logger.warning(f"Playwright failed for {url}: {e}")
            return None

    # ------------------------------------------------------------------
    # Trafilatura ও BeautifulSoup (Fallback)
    # ------------------------------------------------------------------
    def _extract_trafilatura(self, url: str):
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None

            text = trafilatura.extract(
                downloaded,
                include_links=False,
                include_images=False,
                include_tables=True,
                favor_precision=True,
            )

            if not text:
                return None

            metadata = trafilatura.extract_metadata(downloaded)
            title = metadata.title if metadata and metadata.title else ""

            logger.info("Trafilatura extraction successful.")
            return Document(
                page_content=clean_text(text),
                metadata=self._metadata(url, title, "trafilatura"),
            )

        except Exception as e:
            logger.warning(f"Trafilatura failed: {e}")
            return None

    def _extract_bs4(self, url: str):
        try:
            response = session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"

            soup = BeautifulSoup(response.text, "lxml")

            for tag in REMOVE_TAGS:
                for t in soup.find_all(tag):
                    t.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find(class_="entry-content") or
                soup.find(class_="post-content") or
                soup.find(class_="content") or
                soup.body or
                soup
            )

            text = clean_text(main_content.get_text("\n", strip=True))

            if not text or len(text) < 50:
                return None

            logger.info("BeautifulSoup extraction successful.")
            return Document(
                page_content=text,
                metadata=self._metadata(url, title, "beautifulsoup"),
            )

        except Exception as e:
            logger.error(f"BeautifulSoup failed: {e}")
            return None

    def load(self, url: str, retries: int = 2):
        """মূল লোড মেথড: প্রথমে Playwright, তারপর Trafilatura, শেষে BS4"""
        extraction_methods = [
            self._extract_playwright,
            self._extract_trafilatura,
            self._extract_bs4,
        ]

        for attempt in range(retries):
            logger.info(f"Loading {url} (Attempt {attempt+1}/{retries})")
            for method in extraction_methods:
                doc = method(url)
                if doc:
                    logger.info(
                        f"✅ Successfully loaded '{url}' using "
                        f"'{doc.metadata['extraction_method']}'"
                    )
                    return [doc]
            logger.warning(f"Attempt {attempt+1} failed for {url}. Retrying...")

        logger.error(f"❌ Unable to extract content from {url} after {retries} attempts.")
        return []


# ক্লাসের বাইরে সহজে ব্যবহারের জন্য ফাংশন
loader = WebsiteLoader()


def load_website(
    url: str,
    timeout: int = 45,
) -> List[Document]:
    return WebsiteLoader(timeout).load(url)


def load_websites(
    urls: List[str],
    timeout: int = 45,
) -> List[Document]:
    docs = []
    loader_instance = WebsiteLoader(timeout)
    for url in urls:
        docs.extend(loader_instance.load(url))
    return docs