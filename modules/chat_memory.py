"""
modules/chat_memory.py
=======================
Lightweight, dependency-free conversation memory. Keeps a rolling window
of the last N turns per session so the RAG chain can hold a coherent
multi-turn, multilingual conversation without unbounded context growth.
"""

from typing import List, Dict
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ChatMemory:
    """Simple in-memory, per-session chat history with a max turn window."""

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self._sessions: Dict[str, List[BaseMessage]] = {}

    def _ensure_session(self, session_id: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        self._ensure_session(session_id)
        return self._sessions[session_id]

    def add_turn(self, session_id: str, user_text: str, ai_text: str):
        self._ensure_session(session_id)
        history = self._sessions[session_id]
        history.append(HumanMessage(content=user_text))
        history.append(AIMessage(content=ai_text))

        # Keep only the last `max_turns` (user+ai) pairs
        max_messages = self.max_turns * 2
        if len(history) > max_messages:
            self._sessions[session_id] = history[-max_messages:]

    def clear(self, session_id: str):
        self._sessions[session_id] = []

    def as_transcript(self, session_id: str) -> str:
        """Human-readable transcript, useful for exporting/debugging."""
        lines = []
        for msg in self.get_messages(session_id):
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)


# Global singleton used by the Streamlit app (one process = one server)
chat_memory = ChatMemory()
