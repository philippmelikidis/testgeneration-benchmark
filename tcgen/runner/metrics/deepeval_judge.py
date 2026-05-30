"""Semantic evaluation with DeepEval G-Eval (LLM-as-judge).

The judge runs through the same provider abstraction as generation, so it works
locally on Ollama by default. Each metric is measured defensively: a judge
failure yields ``None`` (recorded as "not available") rather than crashing the
experiment.
"""

from __future__ import annotations

import logging

from config.settings import Settings, get_settings
from tcgen.llm import LLMProvider, get_judge_provider
from tcgen.orchestration.models import JudgeScores

log = logging.getLogger(__name__)


def _make_deepeval_model(provider: LLMProvider):
    """Adapt an :class:`LLMProvider` to DeepEval's custom-model interface."""
    from deepeval.models.base_model import DeepEvalBaseLLM

    class _ProviderModel(DeepEvalBaseLLM):
        def __init__(self, prov: LLMProvider):
            self._prov = prov

        def load_model(self):
            return self._prov

        def generate(self, prompt: str, *args, **kwargs) -> str:
            return self._prov.complete(prompt)

        async def a_generate(self, prompt: str, *args, **kwargs) -> str:
            return self.generate(prompt)

        def get_model_name(self) -> str:
            return f"{self._prov.name}:{self._prov.model}"

    return _ProviderModel(provider)


# G-Eval rubrics. For correctness/appropriateness/readability a HIGHER score is
# better; for hallucination a HIGHER score is WORSE (more invented content).
_CRITERIA = {
    "correctness": (
        "Judge whether the Playwright test correctly verifies the behaviour in the "
        "user stories: the actions follow the described flow and the assertions "
        "check the stated acceptance criteria. Higher is better."
    ),
    "appropriateness": (
        "Judge whether the test targets the relevant scenario using appropriate, "
        "user-facing locators (get_by_role/label/text) and web-first assertions, "
        "without irrelevant or redundant steps. Higher is better."
    ),
    "hallucination": (
        "Award a HIGH score when the test references UI elements, routes, or "
        "features NOT implied by the user stories or the explored application. "
        "Award a LOW score when every element used is plausibly grounded."
    ),
    "readability": (
        "Judge readability and maintainability: descriptive test names, clear "
        "structure, comments only where needed, no dead code. Higher is better."
    ),
}


class DeepEvalJudge:
    def __init__(self, settings: Settings | None = None, provider: LLMProvider | None = None):
        self.settings = settings or get_settings()
        self.provider = provider or get_judge_provider(self.settings)

    def judge(self, script_code: str, story_block: str, base_url: str,
              phase=None) -> JudgeScores:
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase, LLMTestCaseParams

        from tcgen.progress import NullPhase

        phase = phase or NullPhase()
        model = _make_deepeval_model(self.provider)
        params = [LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT]
        test_case = LLMTestCase(
            input=f"BASE URL: {base_url}\n\nUSER STORIES:\n{story_block}",
            actual_output=script_code,
        )

        scores: dict[str, float | None] = {}
        reasons: dict[str, str] = {}
        n = len(_CRITERIA)
        for i, (key, criteria) in enumerate(_CRITERIA.items()):
            phase.update(i / n, f"Judge: {key}")
            try:
                metric = GEval(name=key, criteria=criteria,
                               evaluation_params=params, model=model)
                metric.measure(test_case)
                scores[key] = round(float(metric.score), 4)
                reasons[key] = (metric.reason or "")[:500]
            except Exception as exc:  # noqa: BLE001
                log.warning("Judge metric %r failed: %s", key, exc)
                scores[key] = None
                reasons[key] = f"error: {exc}"

        phase.update(1.0, "Judge fertig")
        return JudgeScores(
            correctness=scores.get("correctness"),
            appropriateness=scores.get("appropriateness"),
            hallucination=scores.get("hallucination"),
            readability=scores.get("readability"),
            reasons=reasons,
        )
