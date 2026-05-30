"""Local Ollama backend (default, no API cost).

Requires a running Ollama daemon (``ollama serve``) and a pulled model, e.g.::

    ollama pull qwen2.5-coder:7b
"""

from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from tcgen.llm.base import LLMProvider, Message


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, *, base_url: str = "http://localhost:11434", **kw):
        super().__init__(model, **kw)
        # Imported lazily so the package imports without ollama installed.
        import ollama

        self._client = ollama.Client(host=base_url)
        self.base_url = base_url

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
        resp = self._client.chat(
            model=self.model,
            messages=list(messages),
            options=options,
            format="json" if json_mode else "",
        )
        return resp["message"]["content"]
