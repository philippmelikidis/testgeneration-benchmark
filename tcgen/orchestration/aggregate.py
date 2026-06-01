"""Flatten experiment records into plain rows for tables and charts.

Returns built-in types only (no pandas) so the core stays UI-agnostic; the
Streamlit layer wraps these in DataFrames.
"""

from __future__ import annotations

from tcgen.orchestration.models import ExperimentRecord, PipelineResult

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
