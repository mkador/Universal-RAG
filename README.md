# Universal-RAG
### AI-Powered Multilingual (English + বাংলা) Business Query System

A Retrieval-Augmented Generation (RAG) assistant that lets a business index
its own documents — PDF, Word, Excel, CSV, plain text, Markdown, and web
pages — and then answers employee/customer questions **in whichever
language they ask** (English or Bangla), grounded strictly in those
documents, with source citations.

---

## ✨ Features

- **Multi-format ingestion**: PDF, DOCX, XLSX/XLS, CSV, TXT, Markdown, and website URLs.
- **Bilingual by design**: auto-detects English vs Bangla per question and answers in kind (no need to set a language toggle).
- **Grounded answers**: every answer is built only from retrieved chunks of your own documents; the assistant says clearly when it doesn't know.
- **Source citations**: each answer shows which document (and page/sheet, when applicable) it came from.
- **Persistent vector store**: uses Chroma with on-disk persistence, so you don't need to re-index every restart.
- **Pluggable embeddings**: OpenAI (`text-embedding-3-large`) or a free local multilingual model (`paraphrase-multilingual-mpnet-base-v2`) that supports Bangla well.
- **Conversation memory**: keeps recent chat turns per session for natural follow-up questions.
- **Simple Streamlit UI**: upload files, add a website, rebuild the index, and chat — all from one page.

---

## 🗂️ Project structure

```
Universal-RAG/
│
├── app.py                 # Streamlit UI (upload, index, chat)
├── requirements.txt
├── .env                   # your configuration (API keys, model names, paths)
├── README.md
├── config.py               # loads .env into a single `settings` object
│
├── data/                   # drop source files here (or upload via the UI)
│   ├── pdf/
│   ├── docx/
│   ├── excel/
│   ├── csv/
│   ├── text/
│   └── markdown/
│
├── uploads/                # audit copy of every file uploaded via the UI
├── chroma_db/               # persistent vector store (auto-created)
├── logs/                    # daily log files (auto-created)
├── cache/                   # reserved for future caching use
│
├── assets/
│   ├── logo.png             # optional, shown in the sidebar if present
│   └── banner.png
│
├── modules/
│   ├── __init__.py
│   ├── loaders.py           # pdf / docx / excel / csv / text / markdown loaders
│   ├── website_loader.py    # fetch + clean a web page into a Document
│   ├── splitter.py          # bilingual-aware chunking (handles '।' too)
│   ├── embeddings.py        # OpenAI or multilingual HuggingFace embeddings
│   ├── vectordb.py          # Chroma wrapper: add / dedupe / reset / stats
│   ├── retriever.py         # similarity / MMR retriever factory
│   ├── rag_chain.py         # language detection + prompt + LLM + memory
│   ├── chat_memory.py       # lightweight per-session conversation memory
│   ├── prompt.py            # English & Bangla system prompt templates
│   ├── metadata.py          # citation formatting helpers
│   └── utils.py             # logging, language detection, file helpers
│
└── templates/
    └── chat_export_template.html   # optional HTML export template
```

---

## 🚀 Setup

### 1. Create a virtual environment and install dependencies

```bash
cd Universal-RAG
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

Open `.env` and set at least:

```dotenv
OPENAI_API_KEY=sk-...your-key...
LLM_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=huggingface   # or "openai" if you want OpenAI embeddings too
```

- `OPENAI_API_KEY` is required for the chat model (answer generation).
- `EMBEDDING_PROVIDER=huggingface` (default) runs embeddings **locally for
  free** using a multilingual model that supports Bangla well — no extra
  API cost, but the first run will download the model (~1 GB).
- Set `EMBEDDING_PROVIDER=openai` to instead use OpenAI's
  `text-embedding-3-large` for embeddings (higher quality, costs API credits).

### 3. Add your business documents

Either:
- Drop files directly into `data/pdf`, `data/docx`, `data/excel`, `data/csv`, `data/text`, `data/markdown`, then click **"Scan & index /data folder"** in the app, **or**
- Use the sidebar **file uploader** / **website URL** field once the app is running.

### 4. Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

---

## 💬 Usage

1. In the sidebar, upload documents or paste a website URL, then click the
   matching **ingest** button. Watch the "Indexed chunks" counter grow.
2. Type a question in the chat box — in **English or বাংলা**, it doesn't
   matter. Example:
   - "What is our refund policy?"
   - "আমাদের রিফান্ড নীতি কী?"
3. The assistant retrieves the most relevant chunks from your documents,
   answers in the same language as your question, and shows the source
   document(s) it used under **📎 Sources**.
4. Use **"Rebuild index from scratch"** (Danger zone) if you want to wipe
   the vector store and start over, e.g. after removing outdated documents.

---

## 🔧 Configuration reference (`.env`)

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for the chat LLM | — |
| `LLM_MODEL` | Chat model name | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | Response creativity (0 = deterministic) | `0.2` |
| `EMBEDDING_PROVIDER` | `openai` or `huggingface` | `huggingface` |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-large` |
| `HF_EMBEDDING_MODEL` | Local multilingual embedding model | `paraphrase-multilingual-mpnet-base-v2` |
| `CHROMA_PERSIST_DIR` | Vector store folder | `chroma_db` |
| `CHROMA_COLLECTION_NAME` | Chroma collection name | `universal_rag_business` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Text splitting parameters | `1000` / `150` |
| `TOP_K` | Chunks retrieved per query | `5` |
| `SEARCH_TYPE` | `similarity` or `mmr` | `mmr` |

---

## 🧩 Extending

- **Add a new file format**: add a loader function in `modules/loaders.py`
  and register it in `_LOADER_MAP` + `config.SUPPORTED_EXTENSIONS`.
- **Add a 3rd language**: extend `modules/utils.py::detect_language` and
  add a matching system prompt block in `modules/prompt.py`.
- **Swap the LLM provider**: replace `ChatOpenAI` in `modules/rag_chain.py`
  with another LangChain chat model (e.g. Anthropic, Azure OpenAI, local
  Ollama model).
- **Export chat transcripts**: `templates/chat_export_template.html` is a
  ready-made Jinja2 template you can render with
  `modules/chat_memory.py::as_transcript`.

---

## 📝 Notes

- Bangla text uses the danda `।` as a sentence terminator instead of a
  period — the text splitter (`modules/splitter.py`) accounts for this so
  Bangla documents are chunked at natural sentence boundaries.
- Language detection combines a fast Unicode-range heuristic with
  `langdetect` for robustness on short queries.
- The vector store de-duplicates chunks by content hash, so re-running
  "Scan & index /data folder" after adding a few new files won't create
  duplicate entries for files already indexed.
