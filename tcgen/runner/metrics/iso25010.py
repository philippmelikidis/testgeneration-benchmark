"""Map the raw metric suite onto ISO/IEC 25010 Functional Suitability.

Following the SLR's synthesis mapping (Planning §9):
  * functional correctness / pass behaviour   -> Functional Correctness
  * coverage of the reachable surface          -> Functional Completeness
  * requirement/scenario appropriateness       -> Functional Appropriateness

Each sub-characteristic is in [0, 1] and combines an objective signal with a
semantic signal where both are available.

Design notes (addressing known metric pitfalls):
- **Completeness uses *exercised* coverage** (distinct locators in PASSING tests),
  not the static locator count, so hallucinated locators in failing tests do not
  inflate it.
- The completeness denominator is the **number of interactable elements the
  crawler actually discovered on the app** (passed in by the orchestrator), not a
  magic constant.
- **Executability is continuous** (the pass rate / SSR feeds correctness), not a
  binary 0/1 flag — a suite where 9/10 tests pass scores above one where 1/10
  passes.

Interpretation caveat (Methode 1): the DeepEval judge scores all artefacts
against the user stories as a *common yardstick*, even though the crawler and the
LLM agent never received those stories during generation. Judge-based numbers for
``Skript_C``/``Skript_L`` therefore measure "did the requirement-free suite
happen to cover the requirements", which is exactly the contrast against the
story-aware hybrid ``Skript_H``. Report and discuss it as such.
"""

from __future__ import annotations

from tcgen.orchestration.models import ExecutionResult, Iso25010, JudgeScores


def _mean(*vals: float | None) -> float | None:
    present = [v for v in vals if v is not None]
    return round(sum(present) / len(present), 4) if present else None


def map_to_iso(
    execution: ExecutionResult,
    judge: JudgeScores,
    coverage_denominator: int | None = None,
) -> Iso25010:
    # --- Functional Correctness: assertions hold (continuous pass rate) + judge ---
    correctness = _mean(judge.correctness, execution.ssr)

    # --- Functional Completeness: exercised share of the reachable surface ---
    if coverage_denominator and coverage_denominator > 0:
        completeness: float | None = round(
            min(execution.exercised_coverage / coverage_denominator, 1.0), 4
        )
    else:
        completeness = None

    # --- Functional Appropriateness: on-task + grounded (low hallucination) ---
    grounded = None if judge.hallucination is None else (1.0 - judge.hallucination)
    appropriateness = _mean(judge.appropriateness, grounded)

    return Iso25010(
        functional_correctness=correctness,
        functional_completeness=completeness,
        functional_appropriateness=appropriateness,
    )
