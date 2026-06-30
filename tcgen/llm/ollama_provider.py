"""Ollama backend — local daemon or Ollama Cloud.

Local (default, no API cost): run ``ollama serve`` and pull a model, e.g.
``ollama pull qwen2.5-coder:7b``.

Ollama Cloud (hosted): set ``base_url`` to ``https://ollama.com`` and pass an
``api_key``; the client then authenticates with a Bearer token and can use cloud
models such as ``gpt-oss:120b``.
"""

from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from tcgen.llm.base import LLMProvider, Message


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, *, base_url: str = "http://localhost:11434",
                 api_key: str = "", think: bool = False, request_timeout_s: float = 120.0,
                 **kw):
        super().__init__(model, **kw)
        # Imported lazily so the package imports without ollama installed.
        import ollama

        headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
        # A request timeout is essential: without it a stalled cloud call hangs the
        # whole agent loop indefinitely (each of N exploration steps is a call).
        self._client = ollama.Client(host=base_url, headers=headers,
                                     timeout=request_timeout_s)
        self.base_url = base_url
        self.is_cloud = bool(api_key)
        # Thinking models (glm-5.1, gpt-oss, deepseek) otherwise spend the token
        # budget on reasoning and leave `content` empty/truncated. We disable
        # visible reasoning so the answer (the code) goes straight to `content`.
        self.think = think

    @property
    def name(self) -> str:
        return "ollama"

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
        options = {
            "temperature": self.temperature if temperature is None else temperature,
            "num_predict": self.max_tokens if max_tokens is None else max_tokens,
        }
        kwargs = dict(
            model=self.model,
            messages=list(messages),
            options=options,
            format="json" if json_mode else "",
        )
        try:
            resp = self._client.chat(**kwargs, think=self.think)
        except TypeError:
            # Older ollama-python without the `think` kwarg.
            resp = self._client.chat(**kwargs)
        msg = resp["message"]
        content = msg.get("content") or ""
        if not content.strip():
            # Defensive: if a thinking model still left content empty, fall back
            # to the reasoning text so downstream extraction has something.
            content = msg.get("thinking") or ""
        return content
