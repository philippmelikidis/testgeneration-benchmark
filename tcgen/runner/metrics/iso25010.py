"""Map the raw metric suite onto ISO/IEC 25010 Functional Suitability.

Following the SLR's synthesis mapping (Planning §9):
  * functional correctness / mutation-like signals -> Functional Correctness
  * coverage / executability                       -> Functional Completeness
  * requirement/scenario appropriateness           -> Functional Appropriateness

The standard is used purely as a *framing*, exactly as in the SLR. Each
sub-characteristic is reported in [0, 1] and combines an objective signal
(execution) with a semantic signal (judge) where both are available.
"""

from __future__ import annotations

from tcgen.orchestration.models import ExecutionResult, Iso25010, JudgeScores

# Element-coverage is unbounded; normalise against a soft reference cap so it can
# enter a [0, 1] sub-characteristic. Tune per study; documented as a threat to
# validity rather than an absolute scale.
COVERAGE_REFERENCE = 20


def _mean(*vals: float | None) -> float | None:
    present = [v for v in vals if v is not None]
    return round(sum(present) / len(present), 4) if present else None


def map_to_iso(execution: ExecutionResult, judge: JudgeScores) -> Iso25010:
    # --- Functional Correctness: do assertions hold + does the judge agree? ---
    correctness = _mean(
        judge.correctness,
        execution.ssr if execution.executed else 0.0,
    )

    # --- Functional Completeness: breadth of interaction + executability ---
    norm_cov = min(execution.element_coverage / COVERAGE_REFERENCE, 1.0)
    executability = 1.0 if execution.executed else 0.0
    completeness = _mean(norm_cov, executability)

    # --- Functional Appropriateness: on-task + grounded (low hallucination) ---
    grounded = None if judge.hallucination is None else (1.0 - judge.hallucination)
    appropriateness = _mean(judge.appropriateness, grounded)

    return Iso25010(
        functional_correctness=correctness,
        functional_completeness=completeness,
        functional_appropriateness=appropriateness,
    )
