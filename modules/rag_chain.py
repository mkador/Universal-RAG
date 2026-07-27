"""
modules/rag_chain.py
=====================
Ties together retriever + bilingual prompt + LLM + chat memory into a
single `ask()` function used by app.py. Automatically detects the
language of the incoming question (English or Bangla) and answers in
kind, grounded in the retrieved business documents.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from modules.retriever import get_retriever
from modules.prompt import build_chat_prompt, get_fallback_message
from modules.chat_memory import chat_memory
from modules.metadata import build_context_string, format_sources
from modules.utils import get_logger, detect_language
from langchain_groq import ChatGroq
logger = get_logger(__name__)


@dataclass
class RAGResponse:
    answer: str
    language: str
    sources: List[str] = field(default_factory=list)
    retrieved_docs: List[Document] = field(default_factory=list)
    used_fallback: bool = False


def get_llm(temperature: Optional[float] = None) -> ChatOpenAI:
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please add it to your .env file "
            "to enable the language model."
        )
    return ChatGroq(
        model=settings.LLM_MODEL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        groq_api_key=settings.GROQ_API_KEY,
    )


def ask(
    question: str,
    session_id: str = "default",
    top_k: Optional[int] = None,
    source_filter: Optional[str] = None,
) -> RAGResponse:
    """
    Main entry point: given a user question (English or Bangla), retrieve
    relevant business document chunks, build a grounded bilingual prompt,
    call the LLM, update memory, and return a structured response.
    """
    question = (question or "").strip()
    if not question:
        return RAGResponse(answer="", language="en", used_fallback=True)

    language = detect_language(question)
    logger.info(f"[{session_id}] Question detected as '{language}': {question[:80]}")

    retriever = get_retriever(top_k=top_k, source_filter=source_filter)
    retrieved_docs = retriever.invoke(question)

    if not retrieved_docs:
        fallback = get_fallback_message(language)
        chat_memory.add_turn(session_id, question, fallback)
        return RAGResponse(answer=fallback, language=language, used_fallback=True)

    context = build_context_string(retrieved_docs)
    sources = format_sources(retrieved_docs)

    prompt = build_chat_prompt(language)
    llm = get_llm()
    chain = prompt | llm

    history = chat_memory.get_messages(session_id)

    result = chain.invoke(
        {
            "context": context,
            "question": question,
            "chat_history": history,
        }
    )

    answer = result.content if hasattr(result, "content") else str(result)
    chat_memory.add_turn(session_id, question, answer)

    return RAGResponse(
        answer=answer,
        language=language,
        sources=sources,
        retrieved_docs=retrieved_docs,
        used_fallback=False,
    )
