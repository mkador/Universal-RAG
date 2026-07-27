"""
modules package
================
Core building blocks for the Universal-RAG (English + Bangla) Business
Query System:

- loaders        : load documents from pdf / docx / excel / csv / text / markdown
- website_loader : load & clean content from a web page URL
- splitter       : chunk documents for embedding
- embeddings     : embedding function factory (OpenAI or multilingual HF model)
- vectordb       : Chroma vector store wrapper (create / load / persist)
- retriever      : retriever factory (similarity / MMR)
- prompt         : bilingual (English + Bangla) system & QA prompt templates
- chat_memory    : lightweight conversation memory
- rag_chain      : ties everything together into a single `ask()` function
- metadata       : helpers to build & format source metadata / citations
- utils          : logging, language detection, file helpers
"""
