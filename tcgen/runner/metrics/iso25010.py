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
- The completeness denominator is the **crawler's discovered interactive surface**
  (rep-independent, representative after a deep crawl), passed in by the
  orchestrator. An earlier union-of-exercised-locators denominator was rejected
  because it grows with the repetition count (50 reps of non-deterministic LLM
  output inflate the union), which collapsed completeness and broke cross-run
  comparability. The union is kept only as a fallback when no crawler ran.
- **Executability is continuous** (the pass rate / SSR feeds correctness), not a
  binary 0/1 flag — a suite where 9/10 tests pass scores above one where 1/10
  passes.

Judge inputs are decoupled by method: ``Skript_C``/``Skript_L`` (Methode 1) are
graded *intrinsically* (test quality + grounding to the app), because they were
generated without the user stories; ``Skript_H`` (Methode 2) is graded against
the user stories it was given. This avoids branding real, explored elements as
"hallucinated" just because they are absent from a requirement the pipeline never
saw. Consequence: judge-derived numbers are fair per method but only partially
comparable across Methode 1 vs. Methode 2 — report them as such.
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

    # --- Functional Completeness ---
    # Primary: REQUIREMENT coverage — the share of the specified user stories that
    # a passing test actually verifies (ISO's "covers all specified tasks and user
    # objectives"). This replaces "share of every element in the whole app", which
    # structurally floored a focused suite (a 6-story suite can never touch all ~73
    # discovered affordances). Falls back to exercised-surface coverage only when
    # the target declares no story signatures.
    completeness: float | None
    if execution.story_total:
        completeness = round(execution.story_covered / execution.story_total, 4)
    elif coverage_denominator and coverage_denominator > 0:
        completeness = round(
            min(execution.exercised_coverage / coverage_denominator, 1.0), 4
        )
    else:
        completeness = None

    # --- Functional Appropriateness: the judge's appropriateness score, used
    # identically for every pipeline. Hallucination is reported as a SEPARATE
    # metric (and is n/a for the crawler) rather than folded in here, so that a
    # not-applicable hallucination value cannot change how appropriateness is
    # computed for one pipeline versus another.
    appropriateness = judge.appropriateness

    return Iso25010(
        functional_correctness=correctness,
        functional_completeness=completeness,
        functional_appropriateness=appropriateness,
    )
