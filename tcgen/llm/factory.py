"""Construct providers from :class:`~config.settings.Settings`."""

from __future__ import annotations

from config.settings import Settings, get_settings
from tcgen.llm.base import LLMProvider


def _build(settings: Settings, model: str) -> LLMProvider:
    common = dict(temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens)
    if settings.llm_provider == "ollama":
        from tcgen.llm.ollama_provider import OllamaProvider

        return OllamaProvider(model, base_url=settings.ollama_base_url,
                              api_key=settings.ollama_api_key,
                              think=settings.ollama_think, **common)
    if settings.llm_provider == "openai":
        from tcgen.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(model, api_key=settings.openai_api_key, **common)
    if settings.llm_provider == "gemini":
        from tcgen.llm.gemini_provider import GeminiProvider

        return GeminiProvider(model, api_key=settings.gemini_api_key, **common)
    raise ValueError(f"Unknown provider: {settings.llm_provider!r}")


def get_provider(settings: Settings | None = None) -> LLMProvider:
    """Provider used for generation (LLM agent, hybrid refiner)."""
    settings = settings or get_settings()
    return _build(settings, settings.generation_model)


def get_judge_provider(settings: Settings | None = None) -> LLMProvider:
    """Provider used for the DeepEval judge (may be a stronger model)."""
    settings = settings or get_settings()
    return _build(settings, settings.judge_model)
