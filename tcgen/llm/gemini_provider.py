"""Google Gemini backend via the google-genai SDK (fast, hosted).

Enabled by ``TCGEN_LLM_PROVIDER=gemini`` and ``TCGEN_GEMINI_API_KEY``. Speeds up
the LLM-bound stages (Skript_L synthesis, Skript_H refinement, the judge); the
crawler is browser-bound and unaffected.
"""

from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from tcgen.llm.base import LLMProvider, Message


class GeminiProvider(LLMProvider):
    def __init__(self, model: str, *, api_key: str, **kw):
        super().__init__(model, **kw)
        if not api_key:
            raise ValueError("Gemini provider selected but TCGEN_GEMINI_API_KEY is empty.")
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "google-genai ist nicht installiert. Bitte ausführen: "
                "pip install google-genai (oder pip install -r requirements.txt)."
            ) from exc

        self._genai = genai
        self._client = genai.Client(api_key=api_key)

    @property
    def name(self) -> str:
        return "gemini"

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
        from google.genai import types

        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system") or None
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

        config = types.GenerateContentConfig(
            temperature=self.temperature if temperature is None else temperature,
            max_output_tokens=self.max_tokens if max_tokens is None else max_tokens,
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )
        resp = self._client.models.generate_content(
            model=self.model, contents=contents, config=config
        )
        return resp.text or ""
