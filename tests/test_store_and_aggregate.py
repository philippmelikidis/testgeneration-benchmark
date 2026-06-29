from tcgen.orchestration.aggregate import METRIC_COLUMNS, flatten_result, record_rows
from tcgen.orchestration.models import (
    ExecutionResult,
    ExperimentRecord,
    GeneratedScript,
    Iso25010,
    JudgeScores,
    Pipeline,
    PipelineResult,
)
from tcgen.orchestration.results_store import ResultsStore


def _record():
    script = GeneratedScript(pipeline=Pipeline.CRAWLER, app_key="opencart",
                             code="def test_x(page):\n    pass\n")
    result = PipelineResult(
        script=script,
        execution=ExecutionResult(executed=True, passed=True, n_tests=1,
                                  n_passed=1, ssr=1.0, element_coverage=4),
        judge=JudgeScores(correctness=0.7, appropriateness=0.6, hallucination=0.1),
        iso=Iso25010(functional_correctness=0.8, functional_completeness=0.5,
                     functional_appropriateness=0.7),
    )
    return ExperimentRecord(id="20260529-000000_opencart_abc123", app_key="opencart",
                            app_name="OpenCart Storefront", provider="ollama",
                            model="qwen2.5-coder:7b", pipelines=[result])


def test_results_store_roundtrip(tmp_path):
    store = ResultsStore(directory=tmp_path)
    rec = _record()
    store.save(rec)
    assert store.list_ids() == [rec.id]
    loaded = store.load(rec.id)
    assert loaded.id == rec.id
    assert loaded.pipelines[0].script.pipeline is Pipeline.CRAWLER
    assert loaded.pipelines[0].iso.overall is not None


def test_flatten_result_has_all_metric_columns():
    row = flatten_result(_record().pipelines[0])
    for key, _label, _hib in METRIC_COLUMNS:
        assert key in row, f"missing metric column {key}"
    assert row["script"] == "Skript_C"


def test_record_rows_includes_app_context():
    rows = record_rows(_record())
    assert rows[0]["app"] == "OpenCart Storefront"
    assert rows[0]["pipeline"] == "crawler"


def test_pipeline_by_helper():
    rec = _record()
    assert rec.by_pipeline(Pipeline.CRAWLER) is not None
    assert rec.by_pipeline(Pipeline.HYBRID) is None


def test_record_to_markdown_is_complete():
    from tcgen.orchestration.report import record_to_markdown

    md = record_to_markdown(_record())
    assert "# Ergebnisbericht" in md
    assert "Vergleichstabelle" in md
    assert "Skript_C" in md
    assert "```python" in md           # generated script included
    assert "ISO: Functional Suitability" in md
