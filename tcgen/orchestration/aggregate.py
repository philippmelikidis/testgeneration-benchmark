"""Flatten experiment records into plain rows for tables and charts.

Returns built-in types only (no pandas) so the core stays UI-agnostic; the
Streamlit layer wraps these in DataFrames.
"""

from __future__ import annotations

import statistics

from tcgen.orchestration.models import (
    ExecutionResult,
    ExperimentRecord,
    JudgeScores,
    PipelineResult,
)

# Numeric metrics over which mean/std are computed across repetitions.
_STAT_KEYS = [
    "gen_time_s", "n_tests", "ssr", "exercised_coverage", "element_coverage",
    "flakiness", "duration_s", "correctness", "appropriateness", "hallucination",
    "readability", "iso_correctness", "iso_completeness", "iso_appropriateness",
    "iso_overall",
]

# (column key, human label, "higher is better"?)
METRIC_COLUMNS: list[tuple[str, str, bool | None]] = [
    ("gen_time_s", "Gen-Zeit (s)", False),
    ("executed", "Ausführbar", True),
    ("passed", "Alle Tests grün", True),
    ("n_tests", "# Tests", None),
    ("ssr", "SSR (Pass-Rate)", True),
    ("exercised_coverage", "Element-Coverage (genutzt)", True),
    ("element_coverage", "Element-Coverage (statisch)", None),
    ("flakiness", "Flakiness", False),
    ("duration_s", "Laufzeit (s)", False),
    ("correctness", "Judge: Correctness", True),
    ("appropriateness", "Judge: Appropriateness", True),
    ("hallucination", "Judge: Hallucination", False),
    ("readability", "Judge: Readability", True),
    ("iso_correctness", "ISO: Correctness", True),
    ("iso_completeness", "ISO: Completeness", True),
    ("iso_appropriateness", "ISO: Appropriateness", True),
    ("iso_overall", "ISO: Functional Suitability", True),
]


def flatten_result(result: PipelineResult) -> dict:
    s, e, j, iso = result.script, result.execution, result.judge, result.iso
    return {
        "pipeline": s.pipeline.value,
        "script": s.pipeline.script_label,
        "gen_time_s": s.generation_time_s,
        "executed": e.executed,
        "passed": e.passed,
        "n_tests": e.n_tests,
        "ssr": e.ssr,
        "exercised_coverage": e.exercised_coverage,
        "element_coverage": e.element_coverage,
        "flakiness": e.flakiness,
        "duration_s": e.duration_s,
        "correctness": j.correctness,
        "appropriateness": j.appropriateness,
        "hallucination": j.hallucination,
        "readability": j.readability,
        "iso_correctness": iso.functional_correctness,
        "iso_completeness": iso.functional_completeness,
        "iso_appropriateness": iso.functional_appropriateness,
        "iso_overall": iso.overall,
        "error": result.error,
    }


def record_rows(record: ExperimentRecord) -> list[dict]:
    """One row per pipeline for a single experiment."""
    rows = []
    for r in record.pipelines:
        row = {"app": record.app_name, "app_key": record.app_key, **flatten_result(r)}
        rows.append(row)
    return rows


def records_rows(records: list[ExperimentRecord]) -> list[dict]:
    """Rows across many experiments (app x pipeline)."""
    out: list[dict] = []
    for rec in records:
        out.extend(record_rows(rec))
    return out


# --------------------------------------------------------------------------- #
# Repetition aggregation (mean / std / anomalies across N runs)
# --------------------------------------------------------------------------- #
def _avg(vals: list[float]) -> float:
    return sum(vals) / len(vals)


def mean_execution(execs: list[ExecutionResult]) -> ExecutionResult:
    def avg(attr: str) -> float:
        return _avg([getattr(e, attr) for e in execs])

    union_locators: set[str] = set()
    for e in execs:
        union_locators |= set(e.exercised_locators)
    return ExecutionResult(
        executed=any(e.executed for e in execs),
        passed=sum(1 for e in execs if e.passed) * 2 >= len(execs),  # majority green
        n_tests=round(avg("n_tests")),
        n_passed=round(avg("n_passed")),
        n_failed=round(avg("n_failed")),
        duration_s=round(avg("duration_s"), 2),
        ssr=round(avg("ssr"), 4),
        element_coverage=round(avg("element_coverage")),
        exercised_coverage=round(avg("exercised_coverage")),
        # Union across reps so the cross-pipeline completeness denominator sees
        # every element any rep genuinely exercised.
        exercised_locators=sorted(union_locators),
        flakiness=round(avg("flakiness"), 4),
        first_error=next((e.first_error for e in execs if e.first_error), None),
        stdout=execs[0].stdout,
        stderr=execs[0].stderr,
    )


def mean_judge(judges: list[JudgeScores]) -> JudgeScores:
    def avg(attr: str) -> float | None:
        vals = [getattr(j, attr) for j in judges if getattr(j, attr) is not None]
        return round(_avg(vals), 4) if vals else None

    reasons = next((j.reasons for j in judges if j.reasons), {})
    return JudgeScores(
        correctness=avg("correctness"),
        appropriateness=avg("appropriateness"),
        hallucination=avg("hallucination"),
        readability=avg("readability"),
        reasons=reasons,
    )


def aggregate_stats(reps: list[dict]) -> tuple[dict, list[str]]:
    """From per-run flattened metric dicts, return (std_per_key, anomalies)."""
    std: dict[str, float] = {}
    for key in _STAT_KEYS:
        vals = [
            r[key] for r in reps
            if isinstance(r.get(key), (int, float)) and not isinstance(r.get(key), bool)
        ]
        if len(vals) > 1:
            std[key] = round(statistics.pstdev(vals), 4)

    anomalies: list[str] = []
    n = len(reps)
    green = sum(1 for r in reps if r.get("passed"))
    if 0 < green < n:
        anomalies.append(f"Instabil: in {green}/{n} Läufen alle Tests grün")
    n_tests = [r.get("n_tests") for r in reps if isinstance(r.get("n_tests"), int)]
    if n_tests and max(n_tests) != min(n_tests):
        anomalies.append(f"Unterschiedliche Testanzahl pro Lauf: {min(n_tests)}–{max(n_tests)}")
    for key, s in std.items():
        mean_vals = [r[key] for r in reps if isinstance(r.get(key), (int, float))
                     and not isinstance(r.get(key), bool)]
        m = _avg(mean_vals) if mean_vals else 0.0
        if m and abs(s / m) > 0.4:
            anomalies.append(f"Hohe Varianz bei {key}: {round(m, 3)} ± {s}")
    return std, anomalies
