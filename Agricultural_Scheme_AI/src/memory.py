"""Small, dependency-light helpers for per-session conversational memory."""
from __future__ import annotations

from typing import Any, Iterable
from langchain_core.messages import AIMessage, HumanMessage

MAX_HISTORY_MESSAGES = 12  # six recent user/assistant turns


def _get(message: Any, key: str, default=None):
    if isinstance(message, dict):
        return message.get(key, default)
    return getattr(message, key, default)


def normalize_history(messages: Iterable[Any] | None, limit: int = MAX_HISTORY_MESSAGES) -> list[dict[str, str]]:
    """Validate roles/content and retain only the most recent messages."""
    cleaned: list[dict[str, str]] = []
    for item in messages or []:
        role = _get(item, "role", None)
        content = _get(item, "content", "")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        content = content.strip()
        if content:
            cleaned.append({"role": role, "content": content})
    return cleaned[-max(1, limit):]


def to_langchain_messages(messages: Iterable[Any] | None):
    """Convert API/session history to LangChain HumanMessage/AIMessage objects."""
    result = []
    for item in normalize_history(messages):
        cls = HumanMessage if item["role"] == "user" else AIMessage
        result.append(cls(content=item["content"]))
    return result


def build_retrieval_query(question: str, history: Iterable[Any] | None) -> str:
    """Include recent turns so short follow-up questions retrieve relevant PDFs."""
    recent = normalize_history(history, limit=6)
    if not recent:
        return question.strip()
    history_text = "\n".join(f'{m["role"]}: {m["content"]}' for m in recent)
    return f"Conversation context:\n{history_text}\nCurrent question: {question.strip()}"


def append_turn(history: list[dict[str, str]], question: str, answer: str) -> list[dict[str, str]]:
    """Return bounded history after a completed exchange (does not mutate input)."""
    return normalize_history([*history, {"role": "user", "content": question},
                              {"role": "assistant", "content": answer}])
