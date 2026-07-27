# """
# app.py
# ======
# Streamlit UI for the Universal-RAG (English + Bangla) Business Query
# System. Lets business users:
#   - Upload documents (PDF, DOCX, Excel, CSV, TXT, Markdown) or add a
#     website URL as a knowledge source.
#   - Build / rebuild the vector index.
#   - Chat with the assistant in English or Bangla — it auto-detects the
#     question language and answers in the same language, grounded only
#     in the ingested documents, with source citations.

# Run with:
#     streamlit run app.py
# """

# import uuid
# from pathlib import Path

# import streamlit as st

# from config import settings
# from modules.loaders import load_directory, load_file
# from modules.website_loader import load_website
# from modules.splitter import split_documents
# from modules.vectordb import add_documents, collection_count, list_sources, reset_vectorstore
# from modules.rag_chain import ask
# from modules.utils import save_uploaded_file, get_logger, language_label

# logger = get_logger("app")

# st.set_page_config(
#     page_title=settings.APP_NAME,
#     page_icon="🗂️",
#     layout="wide",
# )

# # ------------------------------------------------------------------
# # Session state
# # ------------------------------------------------------------------
# if "session_id" not in st.session_state:
#     st.session_state.session_id = str(uuid.uuid4())
# if "chat_display" not in st.session_state:
#     st.session_state.chat_display = []  # list of dicts: role, content, sources, lang


# def ingest_and_index(docs):
#     if not docs:
#         return 0
#     chunks = split_documents(docs)
#     added = add_documents(chunks)
#     return added


# # ------------------------------------------------------------------
# # Sidebar — knowledge base management
# # ------------------------------------------------------------------
# with st.sidebar:
#     logo_path = settings.ASSETS_DIR / "logo.png"
#     if logo_path.exists():
#         st.image(str(logo_path), width=160)

#     st.title(settings.APP_NAME)
#     st.caption("English + বাংলা business document assistant (RAG)")

#     st.markdown("---")
#     st.subheader("📚 Knowledge base")

#     indexed_count = collection_count()
#     st.metric("Indexed chunks", indexed_count)

#     with st.expander("📂 Sources currently indexed", expanded=False):
#         sources = list_sources()
#         if sources:
#             for s in sources:
#                 st.write(f"• {s}")
#         else:
#             st.caption("No documents indexed yet.")

#     st.markdown("#### Upload documents")
#     uploaded_files = st.file_uploader(
#         "PDF, DOCX, Excel, CSV, TXT, Markdown",
#         type=["pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md", "markdown"],
#         accept_multiple_files=True,
#     )
#     if st.button("➕ Ingest uploaded files", use_container_width=True, disabled=not uploaded_files):
#         with st.spinner("Reading and indexing uploaded files..."):
#             all_docs = []
#             for uf in uploaded_files:
#                 saved_path = save_uploaded_file(uf.getvalue(), uf.name)
#                 all_docs.extend(load_file(Path(saved_path)))
#             added = ingest_and_index(all_docs)
#         st.success(f"Indexed {added} new chunk(s) from {len(uploaded_files)} file(s).")
#         st.rerun()

#     st.markdown("#### Add a website")
#     website_url = st.text_input("Website URL", placeholder="https://example.com/policy")
#     if st.button("🌐 Ingest website", use_container_width=True, disabled=not website_url):
#         with st.spinner(f"Fetching {website_url} ..."):
#             docs = load_website(website_url)
#             added = ingest_and_index(docs)
#         if added:
#             st.success(f"Indexed {added} new chunk(s) from the website.")
#         else:
#             st.warning("No new content indexed (page may be empty, unreachable, or already indexed).")
#         st.rerun()

#     st.markdown("#### Bulk ingest from /data folder")
#     st.caption("Loads every file already placed under data/pdf, data/docx, data/excel, data/csv, data/text, data/markdown")
#     if st.button("🔄 Scan & index /data folder", use_container_width=True):
#         with st.spinner("Scanning data/ folders..."):
#             docs = load_directory()
#             added = ingest_and_index(docs)
#         st.success(f"Indexed {added} new chunk(s) from the data/ folder.")
#         st.rerun()

#     st.markdown("---")
#     with st.expander("⚠️ Danger zone"):
#         if st.button("🗑️ Rebuild index from scratch", use_container_width=True):
#             reset_vectorstore()
#             st.success("Vector store cleared. Re-ingest your documents to rebuild the index.")
#             st.rerun()

#     st.markdown("---")
#     st.caption(
#         f"Embedding provider: `{settings.EMBEDDING_PROVIDER}`  \n"
#         f"LLM model: `{settings.LLM_MODEL}`  \n"
#         f"Top-K retrieval: `{settings.TOP_K}` ({settings.SEARCH_TYPE})"
#     )

# # ------------------------------------------------------------------
# # Main — chat interface
# # ------------------------------------------------------------------
# st.header("💬 Ask your business question")
# st.caption(
#     "Ask in English or Bangla — I'll detect the language and answer in kind, "
#     "using only your uploaded business documents. / ইংরেজি অথবা বাংলায় জিজ্ঞাসা করুন।"
# )

# if not settings.GOOGLE_API_KEY:
#     st.warning(
#         "⚠️ `GOOGLE_API_KEY` is not set in your `.env` file. The chat model "
#         "will not work until you add a valid key.",
#         icon="⚠️",
#     )

# # Render existing chat history
# for turn in st.session_state.chat_display:
#     with st.chat_message(turn["role"]):
#         st.markdown(turn["content"])
#         if turn.get("sources"):
#             with st.expander("📎 Sources"):
#                 for s in turn["sources"]:
#                     st.write(f"• {s}")

# user_question = st.chat_input("Type your question in English or Bangla... / আপনার প্রশ্ন লিখুন...")

# if user_question:
#     st.session_state.chat_display.append({"role": "user", "content": user_question})
#     with st.chat_message("user"):
#         st.markdown(user_question)

#     with st.chat_message("assistant"):
#         if collection_count() == 0:
#             msg = (
#                 "No documents are indexed yet. Please upload files or a website "
#                 "from the sidebar first. / এখনো কোনো ডকুমেন্ট ইনডেক্স করা হয়নি। "
#                 "প্রথমে সাইডবার থেকে ফাইল বা ওয়েবসাইট যোগ করুন।"
#             )
#             st.markdown(msg)
#             st.session_state.chat_display.append({"role": "assistant", "content": msg})
#         else:
#             with st.spinner("Thinking... / চিন্তা করছি..."):
#                 try:
#                     response = ask(user_question, session_id=st.session_state.session_id)
#                 except RuntimeError as e:
#                     response = None
#                     st.error(str(e))

#             if response is not None:
#                 st.markdown(response.answer)
#                 st.caption(f"Detected language: {language_label(response.language)}")
#                 if response.sources:
#                     with st.expander("📎 Sources"):
#                         for s in response.sources:
#                             st.write(f"• {s}")

#                 st.session_state.chat_display.append(
#                     {
#                         "role": "assistant",
#                         "content": response.answer,
#                         "sources": response.sources,
#                     }
#                 )

# st.markdown("---")
# st.caption("Universal-RAG • Multilingual (English + Bangla) Business Query System")



"""
app.py
======
Streamlit UI for the Universal-RAG (English + Bangla) Business Query
System. Lets business users:
  - Upload documents (PDF, DOCX, Excel, CSV, TXT, Markdown) or add a
    website URL as a knowledge source.
  - Build / rebuild the vector index.
  - Chat with the assistant in English or Bangla — it auto-detects the
    question language and answers in the same language, grounded only
    in the ingested documents, with source citations.

Run with:
    streamlit run app.py
"""

import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as PDFTTFont
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from config import settings
from modules.loaders import load_directory, load_file
from modules.website_loader import load_website
from modules.splitter import split_documents
from modules.vectordb import add_documents, collection_count, list_sources, reset_vectorstore
from modules.rag_chain import ask
from modules.chat_memory import chat_memory
from modules.utils import save_uploaded_file, get_logger, language_label

logger = get_logger("app")

st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Global styling — clean, light theme with a dedicated top navbar
# ------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Hind+Siliguri:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --ink: #1e2433;          /* main text color - dark, high contrast */
            --ink-soft: #4b5468;     /* secondary text */
            --muted: #8891a5;        /* tertiary / captions */
            --accent: #4f46e5;       /* indigo accent */
            --accent-dark: #4338ca;
            --accent-soft: #eef0fe;
            --bg: #f6f7fb;           /* app background */
            --surface: #ffffff;      /* cards / panels */
            --border: #e6e8f0;
            --navy: #0f1729;         /* deep navy for navbar + hero */
            --navy-2: #182238;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', 'Hind Siliguri', 'Noto Sans Bengali', sans-serif;
            color: var(--ink);
        }
        #MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden;}

        .stApp { background: var(--bg); }

        .block-container { padding-top: 1.2rem; max-width: 1180px; }

        /* Force consistent, readable dark text everywhere in the main area,
           regardless of the visitor's browser/OS theme preference. */
        section.main, section.main p, section.main span, section.main li,
        section.main label, section.main h1, section.main h2, section.main h3,
        section.main h4, section.main h5, section.main h6,
        div[data-testid="stChatMessage"], div[data-testid="stChatMessage"] * ,
        div[data-testid="stExpander"] p, div[data-testid="stExpander"] span,
        div[data-testid="stExpander"] li {
            color: var(--ink) !important;
        }
        section.main .stCaption, section.main small { color: var(--muted) !important; }

        /* ---------- Top navigation bar ---------- */
        .top-nav {
            background: linear-gradient(120deg, var(--navy) 0%, var(--navy-2) 100%);
            border-radius: 16px;
            padding: 0.9rem 1.4rem;
            margin-bottom: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.7rem;
            box-shadow: 0 10px 24px rgba(15, 23, 41, 0.18);
        }
        section.main .top-nav, section.main .top-nav *,
        div[data-testid="stMarkdownContainer"] .top-nav,
        div[data-testid="stMarkdownContainer"] .top-nav * { color: #f3f4fb !important; }
        .top-nav-brand { display: flex; align-items: center; gap: 0.65rem; }
        .top-nav-brand .mark {
            width: 36px; height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--accent), #7c6ef2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.05rem;
        }
        .top-nav-brand .name { font-size: 1.02rem; font-weight: 800; line-height: 1.2; }
        section.main .top-nav-brand .tag,
        div[data-testid="stMarkdownContainer"] .top-nav-brand .tag { font-size: 0.72rem; color: #9aa1c2 !important; }
        .top-nav-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        .nav-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .nav-pill b { color: #ffffff !important; font-weight: 700; }

        /* ---------- Hero card ---------- */
        .hero-banner {
            position: relative;
            background: linear-gradient(135deg, var(--navy) 0%, #23305a 55%, #34206b 100%);
            padding: 2.5rem 2.5rem;
            border-radius: 18px;
            margin-bottom: 1.6rem;
            box-shadow: 0 16px 34px rgba(15, 23, 41, 0.28);
            overflow: hidden;
        }
        .hero-banner::after {
            content: "";
            position: absolute;
            inset: 0;
            background-image: radial-gradient(rgba(255,255,255,0.09) 1px, transparent 1px);
            background-size: 22px 22px;
            opacity: 0.4;
            pointer-events: none;
        }
        .hero-banner::before {
            content: "";
            position: absolute;
            top: -80px; right: -80px;
            width: 280px; height: 280px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(124,110,242,0.35), transparent 70%);
        }
        section.main .hero-banner, section.main .hero-banner *,
        div[data-testid="stMarkdownContainer"] .hero-banner,
        div[data-testid="stMarkdownContainer"] .hero-banner * { color: #ffffff !important; }
        section.main .hero-banner p,
        div[data-testid="stMarkdownContainer"] .hero-banner p { color: #dcdcf2 !important; }
        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.18);
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            margin-bottom: 1rem;
            position: relative;
        }
        .hero-banner h1 {
            margin: 0;
            font-size: 2.15rem;
            font-weight: 800;
            letter-spacing: -0.4px;
            line-height: 1.28;
            position: relative;
        }
        .hero-banner p {
            margin: 0.65rem 0 0 0;
            font-size: 1.02rem;
            line-height: 1.7;
            max-width: 760px;
            position: relative;
        }

        /* ---------- Sidebar (clean light panel) ---------- */
        section[data-testid="stSidebar"] {
            background: var(--surface);
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] * { color: var(--ink) !important; }
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] small { color: var(--muted) !important; }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.2rem 0 0.4rem 0;
        }
        .sidebar-brand .mark {
            width: 42px; height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 6px 14px rgba(79,70,229,0.3);
        }
        .sidebar-brand .name { font-size: 1.05rem; font-weight: 800; line-height: 1.2; }
        .sidebar-brand .tag { font-size: 0.78rem; color: var(--muted); }

        .sidebar-section-title {
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent-dark);
            background: var(--accent-soft);
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 8px;
            margin: 1.1rem 0 0.7rem 0;
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--border);
            margin: 1.1rem 0;
        }
        section[data-testid="stSidebar"] [data-testid="stMetric"] {
            background: var(--accent-soft);
            border: 1px solid #dcdffc;
            border-radius: 14px;
            padding: 0.7rem 1rem;
        }
        section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: var(--accent-dark) !important;
            font-weight: 800;
        }
        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: var(--ink-soft) !important;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] .stButton>button,
        section[data-testid="stSidebar"] .stDownloadButton>button {
            background: var(--accent);
            color: #ffffff !important;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.88rem;
            padding: 0.6rem 0.9rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
            box-shadow: 0 6px 14px rgba(79,70,229,0.22);
        }
        section[data-testid="stSidebar"] .stButton>button p,
        section[data-testid="stSidebar"] .stDownloadButton>button p { color: #ffffff !important; font-weight: 700; }
        section[data-testid="stSidebar"] .stButton>button:hover,
        section[data-testid="stSidebar"] .stDownloadButton>button:hover {
            background: var(--accent-dark);
            transform: translateY(-1px);
            box-shadow: 0 10px 20px rgba(79,70,229,0.3);
        }
        section[data-testid="stSidebar"] .stButton>button:disabled,
        section[data-testid="stSidebar"] .stDownloadButton>button:disabled {
            background: #eceefc;
            box-shadow: none;
        }
        section[data-testid="stSidebar"] .stButton>button:disabled p,
        section[data-testid="stSidebar"] .stDownloadButton>button:disabled p { color: #a7acc9 !important; }
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            background: #f8f9fd !important;
            border: 1.5px solid var(--border) !important;
            border-radius: 9px !important;
            color: var(--ink) !important;
        }
        section[data-testid="stSidebar"] input:focus {
            border-color: var(--accent) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            background: #f8f9fd;
            border: 1.5px dashed #c7cbf0;
            border-radius: 14px;
            padding: 0.6rem;
        }
        /* "Browse files" button + helper text inside the uploader */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] section {
            background: transparent !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
            background: #ffffff !important;
            color: var(--accent-dark) !important;
            border: 1.5px solid #dcdffc !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {
            background: var(--accent-soft) !important;
            border-color: var(--accent) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
            color: var(--ink-soft) !important;
        }
        /* uploaded file chip row */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] * {
            color: var(--ink) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] {
            background: #f8f9fd;
            border: 1px solid var(--border);
            border-radius: 12px;
        }
        section[data-testid="stSidebar"] [data-testid="stAlert"] {
            border-radius: 10px;
        }

        /* ---------- Status card row ---------- */
        .status-card {
            background: var(--surface);
            border-radius: 16px;
            padding: 1.05rem 1.2rem;
            box-shadow: 0 8px 20px rgba(30, 36, 51, 0.05);
            border: 1px solid var(--border);
        }
        .status-card .icon { font-size: 1.3rem; }
        .status-card .label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: var(--muted) !important;
            margin-top: 0.35rem;
        }
        .status-card .value {
            font-size: 1.7rem;
            font-weight: 800;
            color: var(--ink) !important;
            margin-top: 0.1rem;
        }

        /* ---------- Chat area ---------- */
        div[data-testid="stChatMessage"] {
            border-radius: 16px;
            padding: 0.4rem 0.5rem;
            margin-bottom: 0.7rem;
            border: 1px solid var(--border);
            box-shadow: 0 4px 14px rgba(30, 36, 51, 0.04);
            background: var(--surface);
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            background: var(--accent-soft);
            border-color: #dcdffc;
        }

        /* ---------- Chat input ---------- */
        div[data-testid="stChatInput"] {
            border-radius: 14px !important;
            border: 1.5px solid var(--border) !important;
            box-shadow: 0 6px 18px rgba(30,36,51,0.05) !important;
            background: var(--surface) !important;
        }
        div[data-testid="stChatInput"]:focus-within {
            border-color: var(--accent) !important;
        }
        div[data-testid="stChatInput"] textarea { color: var(--ink) !important; }

        /* ---------- Badges / misc ---------- */
        .lang-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: var(--accent-soft);
            color: var(--accent-dark) !important;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            margin-top: 0.45rem;
            border: 1px solid #dcdffc;
        }
        .lang-badge * { color: var(--accent-dark) !important; }
        .streamlit-expanderHeader { font-weight: 600; }

        .footer-note, .footer-note * {
            text-align: center;
            color: var(--muted) !important;
            font-size: 0.83rem;
            padding: 1.2rem 0 1.4rem 0;
            letter-spacing: 0.02em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []  # list of dicts: role, content, sources, lang


def ingest_and_index(docs):
    if not docs:
        return 0
    chunks = split_documents(docs)
    added = add_documents(chunks)
    return added


# ------------------------------------------------------------------
# PDF chat export — Bangla + English aware
# ------------------------------------------------------------------
FONT_DIR = settings.ASSETS_DIR / "fonts"
BANGLA_RE = re.compile(r"[\u0980-\u09FF]")


@st.cache_resource(show_spinner=False)
def _register_pdf_fonts():
    """Register the bundled Noto fonts with reportlab exactly once per process."""
    pdfmetrics.registerFont(PDFTTFont("NotoSans", str(FONT_DIR / "NotoSans-Regular.ttf")))
    pdfmetrics.registerFont(PDFTTFont("NotoSans-Bold", str(FONT_DIR / "NotoSans-Bold.ttf")))
    pdfmetrics.registerFont(PDFTTFont("NotoSansBengali", str(FONT_DIR / "NotoSansBengali-Regular.ttf")))
    pdfmetrics.registerFont(PDFTTFont("NotoSansBengali-Bold", str(FONT_DIR / "NotoSansBengali-Bold.ttf")))
    return True


def _classify_char(ch: str) -> str:
    return "bn" if "\u0980" <= ch <= "\u09FF" else "other"


def _bangla_aware_markup(text: str, bold: bool = False) -> str:
    """
    Split text into Bangla vs. non-Bangla runs and wrap Bangla runs in a
    <font name="NotoSansBengali"> tag so a single Paragraph can mix both
    scripts correctly (the Bangla font has no Latin glyphs and vice versa).
    """
    if not text:
        return ""
    runs, cur_class, cur_chars = [], None, []
    for ch in text:
        c = _classify_char(ch)
        if c != cur_class and cur_chars:
            runs.append((cur_class, "".join(cur_chars)))
            cur_chars = []
        cur_class = c
        cur_chars.append(ch)
    if cur_chars:
        runs.append((cur_class, "".join(cur_chars)))

    bn_font = "NotoSansBengali-Bold" if bold else "NotoSansBengali"
    parts = []
    for cls, chunk in runs:
        escaped = xml_escape(chunk).replace("\n", "<br/>")
        parts.append(f'<font name="{bn_font}">{escaped}</font>' if cls == "bn" else escaped)
    return "".join(parts)


def build_chat_export_pdf(chat_display, app_name: str) -> bytes:
    """Render the chat history as a clean, branded PDF transcript."""
    _register_pdf_fonts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title=f"{app_name} - Chat Export",
    )

    accent = colors.HexColor("#4338ca")
    accent_soft = colors.HexColor("#eef0fe")
    ink = colors.HexColor("#1e2433")
    muted = colors.HexColor("#6b7280")
    border = colors.HexColor("#e6e8f0")

    title_style = ParagraphStyle("Title", fontName="NotoSans-Bold", fontSize=18, textColor=accent, leading=22)
    meta_style = ParagraphStyle("Meta", fontName="NotoSans", fontSize=9, textColor=muted, spaceAfter=14)
    role_user_style = ParagraphStyle("RoleUser", fontName="NotoSans-Bold", fontSize=9.5, textColor=accent, spaceAfter=4, alignment=TA_LEFT)
    role_assistant_style = ParagraphStyle("RoleAssistant", fontName="NotoSans-Bold", fontSize=9.5, textColor=ink, spaceAfter=4, alignment=TA_LEFT)
    body_style = ParagraphStyle("Body", fontName="NotoSans", fontSize=10.5, textColor=ink, leading=15.5)
    source_label_style = ParagraphStyle("SourceLabel", fontName="NotoSans-Bold", fontSize=8.5, textColor=muted, spaceBefore=6)
    source_item_style = ParagraphStyle("SourceItem", fontName="NotoSans", fontSize=8.5, textColor=muted, leading=12, leftIndent=10)

    story = [
        Paragraph(xml_escape(app_name), title_style),
        Paragraph(f"Chat export &middot; Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style),
        HRFlowable(width="100%", thickness=1, color=border, spaceAfter=14),
    ]

    for turn in chat_display:
        is_user = turn["role"] == "user"
        role_style = role_user_style if is_user else role_assistant_style
        cell_content = [
            Paragraph("You" if is_user else "Assistant", role_style),
            Paragraph(_bangla_aware_markup(turn["content"]), body_style),
        ]
        sources = turn.get("sources")
        if sources:
            cell_content.append(Paragraph("Sources", source_label_style))
            for s in sources:
                cell_content.append(Paragraph(f"&bull; {xml_escape(str(s))}", source_item_style))

        bubble = Table([[cell_content]], colWidths=[doc.width])
        bubble.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent_soft if is_user else colors.white),
            ("BOX", (0, 0), (-1, -1), 0.75, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(bubble)
        story.append(Spacer(1, 10))

    if not chat_display:
        story.append(Paragraph("No conversation yet.", body_style))

    doc.build(story)
    return buf.getvalue()


# ------------------------------------------------------------------
# Sidebar — knowledge base management
# ------------------------------------------------------------------
with st.sidebar:
    logo_path = settings.ASSETS_DIR / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=140)

    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="mark">🗂️</div>
            <div>
                <div class="name">{settings.APP_NAME}</div>
                <div class="tag">English + বাংলা document assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section-title">📚 Knowledge base</div>', unsafe_allow_html=True)

    indexed_count = collection_count()
    st.metric("Indexed chunks", indexed_count)

    with st.expander("📂 Sources currently indexed", expanded=False):
        sources = list_sources()
        if sources:
            for s in sources:
                st.write(f"• {s}")
        else:
            st.caption("No documents indexed yet.")

    st.markdown('<div class="sidebar-section-title">📤 Upload documents</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "PDF, DOCX, Excel, CSV, TXT, Markdown",
        type=["pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md", "markdown"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if st.button("➕ Ingest uploaded files", use_container_width=True, disabled=not uploaded_files):
        with st.spinner("Reading and indexing uploaded files..."):
            all_docs = []
            for uf in uploaded_files:
                saved_path = save_uploaded_file(uf.getvalue(), uf.name)
                all_docs.extend(load_file(Path(saved_path)))
            added = ingest_and_index(all_docs)
        st.success(f"Indexed {added} new chunk(s) from {len(uploaded_files)} file(s).")
        st.rerun()

    st.markdown('<div class="sidebar-section-title">🌐 Add a website</div>', unsafe_allow_html=True)
    website_url = st.text_input(
        "Website URL", placeholder="https://example.com/policy", label_visibility="collapsed"
    )
    if st.button("🌐 Ingest website", use_container_width=True, disabled=not website_url):
        with st.spinner(f"Fetching {website_url} ..."):
            docs = load_website(website_url)
            added = ingest_and_index(docs)
        if added:
            st.success(f"Indexed {added} new chunk(s) from the website.")
        else:
            st.warning("No new content indexed (page may be empty, unreachable, or already indexed).")
        st.rerun()

    st.markdown('<div class="sidebar-section-title">🔄 Bulk ingest</div>', unsafe_allow_html=True)
    st.caption("Loads every file already placed under data/pdf, data/docx, data/excel, data/csv, data/text, data/markdown")
    if st.button("🔄 Scan & index /data folder", use_container_width=True):
        with st.spinner("Scanning data/ folders..."):
            docs = load_directory()
            added = ingest_and_index(docs)
        st.success(f"Indexed {added} new chunk(s) from the data/ folder.")
        st.rerun()

    st.markdown('<div class="sidebar-section-title">💾 Chat history</div>', unsafe_allow_html=True)
    has_chat = bool(st.session_state.chat_display)
    hist_cols = st.columns(2)
    with hist_cols[0]:
        if has_chat:
            st.download_button(
                "⬇️ Export as PDF",
                data=build_chat_export_pdf(st.session_state.chat_display, settings.APP_NAME),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("⬇️ Export as PDF", use_container_width=True, disabled=True)
    with hist_cols[1]:
        if st.button("🧹 Clear chat", use_container_width=True, disabled=not has_chat):
            st.session_state.chat_display = []
            chat_memory.clear(st.session_state.session_id)
            st.success("Chat history cleared.")
            st.rerun()
    if not has_chat:
        st.caption("Ask a question first — then you can export or clear the conversation.")

    st.markdown("---")
    with st.expander("⚠️ Danger zone"):
        if st.button("🗑️ Rebuild index from scratch", use_container_width=True):
            reset_vectorstore()
            st.success("Vector store cleared. Re-ingest your documents to rebuild the index.")
            st.rerun()

# ------------------------------------------------------------------
# Top navigation bar — branding + system config at a glance
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="top-nav">
        <div class="top-nav-brand">
            <div class="mark">🗂️</div>
            <div>
                <div class="name">{settings.APP_NAME}</div>
                <div class="tag">English + বাংলা business document assistant</div>
            </div>
        </div>
        <div class="top-nav-pills">
            <span class="nav-pill">🔎 Embedding <b>{settings.EMBEDDING_PROVIDER}</b></span>
            <span class="nav-pill">🤖 LLM <b>{settings.LLM_MODEL}</b></span>
            <span class="nav-pill">🎯 Top-K <b>{settings.TOP_K}</b> ({settings.SEARCH_TYPE})</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Main — chat interface
# ------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-eyebrow">✦ Multilingual RAG Assistant</div>
        <h1>Ask your business question</h1>
        <p>Ask in English or Bangla — I'll detect the language and answer in kind,
        grounded strictly in your uploaded business documents, with full source citations.<br>
        ইংরেজি অথবা বাংলায় জিজ্ঞাসা করুন। আমি ভাষা শনাক্ত করে একই ভাষায় উত্তর দেব।</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not settings.GOOGLE_API_KEY:
    st.warning(
        "⚠️ `GOOGLE_API_KEY` is not set in your `.env` file. The chat model "
        "will not work until you add a valid key.",
        icon="⚠️",
    )

status_cols = st.columns(2)
with status_cols[0]:
    st.markdown(
        f"""<div class="status-card"><div class="icon">📦</div>
        <div class="label">Indexed chunks</div>
        <div class="value">{indexed_count}</div></div>""",
        unsafe_allow_html=True,
    )
with status_cols[1]:
    st.markdown(
        f"""<div class="status-card"><div class="icon">🗃️</div>
        <div class="label">Sources loaded</div>
        <div class="value">{len(list_sources())}</div></div>""",
        unsafe_allow_html=True,
    )

st.write("")

# Render existing chat history
for turn in st.session_state.chat_display:
    avatar = "🧑‍💼" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])
        if turn.get("sources"):
            with st.expander("📎 Sources"):
                for s in turn["sources"]:
                    st.write(f"• {s}")

user_question = st.chat_input("Type your question in English or Bangla... / আপনার প্রশ্ন লিখুন...")

if user_question:
    st.session_state.chat_display.append({"role": "user", "content": user_question})
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_question)

    with st.chat_message("assistant", avatar="🤖"):
        if collection_count() == 0:
            msg = (
                "No documents are indexed yet. Please upload files or a website "
                "from the sidebar first. / এখনো কোনো ডকুমেন্ট ইনডেক্স করা হয়নি। "
                "প্রথমে সাইডবার থেকে ফাইল বা ওয়েবসাইট যোগ করুন।"
            )
            st.markdown(msg)
            st.session_state.chat_display.append({"role": "assistant", "content": msg})
        else:
            with st.spinner("Thinking... / চিন্তা করছি..."):
                try:
                    response = ask(user_question, session_id=st.session_state.session_id)
                except RuntimeError as e:
                    response = None
                    st.error(str(e))

            if response is not None:
                st.markdown(response.answer)
                st.markdown(
                    f'<span class="lang-badge">🌐 {language_label(response.language)}</span>',
                    unsafe_allow_html=True,
                )
                if response.sources:
                    with st.expander("📎 Sources"):
                        for s in response.sources:
                            st.write(f"• {s}")

                st.session_state.chat_display.append(
                    {
                        "role": "assistant",
                        "content": response.answer,
                        "sources": response.sources,
                    }
                )

st.markdown(
    """
    <div class="footer-note">✦ Universal-RAG &nbsp;·&nbsp; Multilingual (English + Bangla) Business Query System</div>
    """,
    unsafe_allow_html=True,
)