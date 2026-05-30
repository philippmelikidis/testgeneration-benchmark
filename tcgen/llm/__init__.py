"""LLM provider abstraction.

A single, narrow interface (:class:`LLMProvider`) is implemented by both the
local Ollama backend (default, free) and the OpenAI backend (opt-in). The agent
and the DeepEval judge depend only on this interface, so swapping providers is a
config change, not a code change.
"""

from tcgen.llm.base import LLMProvider, Message
from tcgen.llm.factory import get_judge_provider, get_provider

__all__ = ["LLMProvider", "Message", "get_provider", "get_judge_provider"]
