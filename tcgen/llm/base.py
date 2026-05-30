"""Provider-agnostic chat interface."""

from __future__ import annotations

import abc
from typing import TypedDict


class Message(TypedDict):
    """A single chat message in the OpenAI/Ollama-compatible shape."""

    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(abc.ABC):
    """Minimal chat interface shared by all backends.

    Intentionally text-in/text-out: the agent uses a portable JSON-action
    protocol rather than vendor-specific native tool-calling, so that small
    local Ollama models (which often lack reliable function-calling) work the
    same way as hosted models.
    """

    def __init__(self, model: str, *, temperature: float = 0.1, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short provider identifier, e.g. ``"ollama"``."""

    @abc.abstractmethod
    def chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Return the assistant's reply text for ``messages``.

        ``json_mode`` requests that the backend constrain output to valid JSON
        where supported (best-effort; callers must still parse defensively).
        """

    def complete(self, prompt: str, *, system: str | None = None, **kw) -> str:
        """Convenience single-turn helper."""
        messages: list[Message] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kw)
