"""OpenAI backend (opt-in, requires an API key).

Enabled by setting ``TCGEN_LLM_PROVIDER=openai`` and ``TCGEN_OPENAI_API_KEY``.
"""

from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from tcgen.llm.base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, *, api_key: str, **kw):
        super().__init__(model, **kw)
        if not api_key:
            raise ValueError(
                "OpenAI provider selected but TCGEN_OPENAI_API_KEY is empty."
            )
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    @property
    def name(self) -> str:
        return "openai"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "messages": list(messages),
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
