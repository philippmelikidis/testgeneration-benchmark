"""Render an experiment record into a self-contained Markdown report.

Used by the UI export so a full result (metrics, std, anomalies, judge reasons,
first errors, and the generated scripts) can be downloaded as one file instead
of copied piece by piece.
"""

from __future__ import annotations

from tcgen.orchestration.aggregate import METRIC_COLUMNS, flatten_result
from tcgen.orchestration.models import ExperimentRecord

_ARROW = {True: " (↑)", False: " (↓)", None: ""}


def _fmt(v, digits: int = 3) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _cell(value, std) -> str:
    base = _fmt(value)
    if std and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{base} ± {std:.3f}"
    return base


def record_to_markdown(record: ExperimentRecord, *, include_scripts: bool = True) -> str:
    rows = [flatten_result(r) for r in record.pipelines]
    labels = [r["script"] for r in rows]
    std_by = {r.script.pipeline.script_label: r.metric_std for r in record.pipelines}

    out: list[str] = []
    out.append(f"# Ergebnisbericht — {record.app_name}")
    out.append("")
    out.append(f"- Experiment: `{record.id}`")
    out.append(f"- Provider / Modell: `{record.provider}` / `{record.model}`")
    out.append(f"- Zeitpunkt: {record.created_at}")
    if record.notes:
        out.append(f"- Notes: {record.notes.strip()}")
    out.append("")

    # --- comparison table ---
    out.append("## Vergleichstabelle — Metrik × Pipeline")
    out.append("")
    out.append("| Metrik | " + " | ".join(labels) + " |")
    out.append("|---|" + "---|" * len(labels))
    for key, label, higher in METRIC_COLUMNS:
        cells = [_cell(row.get(key), std_by.get(row["script"], {}).get(key)) for row in rows]
        out.append(f"| {label}{_ARROW[higher]} | " + " | ".join(cells) + " |")
    out.append("")
    out.append("n/a = für diese Pipeline nicht anwendbar. ± x = Std über die Wiederholungen.")
    out.append("")

    # --- anomalies ---
    anomalies = [(r.script.pipeline.script_label, r.anomalies)
                 for r in record.pipelines if r.anomalies]
    if anomalies:
        out.append("## Auffälligkeiten (über die Wiederholungen)")
        out.append("")
        for lab, items in anomalies:
            out.append(f"**{lab}**")
            out.extend(f"- {x}" for x in items)
            out.append("")

    # --- per-pipeline detail ---
    out.append("## Detail je Pipeline")
    out.append("")
    for r in record.pipelines:
        s = r.script
        out.append(f"### {s.pipeline.script_label} ({s.pipeline.value}) · {r.n_runs}×")
        out.append(f"- Generierungszeit: {_fmt(s.generation_time_s)} s · "
                   f"Modell: `{s.model}` · Provider: `{s.provider}`")
        if r.error:
            out.append(f"- Fehler: {r.error}")
        if r.execution.first_error:
            out.append(f"- Erster Test-Fehler: {r.execution.first_error}")
        if s.meta:
            out.append(f"- Meta: `{s.meta}`")
        if r.judge.reasons:
            out.append("- Judge-Begründungen:")
            for k, v in r.judge.reasons.items():
                out.append(f"  - **{k}**: {str(v).strip()}")
        if include_scripts and s.code.strip():
            out.append("")
            out.append(f"<details><summary>{s.pipeline.script_label} — Code</summary>")
            out.append("")
            out.append("```python")
            out.append(s.code.rstrip())
            out.append("```")
            out.append("</details>")
        out.append("")

    return "\n".join(out)
