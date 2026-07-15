"""Results dashboard: comparison table, ISO breakdown, charts, per-pipeline detail."""

from __future__ import annotations

import ui_helpers as ui

ui.setup_page("Ergebnisse")
ui.sidebar_status()

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from tcgen.orchestration.aggregate import METRIC_COLUMNS, flatten_result  # noqa: E402
from tcgen.orchestration.models import Pipeline  # noqa: E402
from tcgen.orchestration.results_store import ResultsStore  # noqa: E402

ui.header("Ergebnisse", "Vergleich der Pipelines auf einer Ziel-App.")

store = ResultsStore()
ids = store.list_ids()
if not ids:
    st.info("Noch keine Experimente. Starte einen Lauf auf der Seite „Experiment starten“.")
    st.stop()


def _parse_id(rid: str) -> tuple[str, str]:
    """(timestamp, app_key) from '<YYYYMMDD-HHMMSS>_<app_key>_<hex6>'."""
    parts = rid.split("_")
    ts = parts[0] if parts else rid
    app = "_".join(parts[1:-1]) if len(parts) >= 3 else "?"
    return ts, app


def _fmt_ts(ts: str) -> str:
    return (f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}"
            if len(ts) >= 13 and "-" in ts else ts)


_parsed = {rid: _parse_id(rid) for rid in ids}
_apps = sorted({app for _, app in _parsed.values()})

# App-Filter zuerst: Läufe sind pro Ziel-App getrennt gespeichert und werden nie
# überschrieben — hier lassen sie sich klar auseinanderhalten.
fcol, scol = st.columns([1, 2])
with fcol:
    app_filter = st.selectbox("Ziel-App", ["(alle Apps)"] + _apps,
                              help="Jeder Lauf gehört zu genau einer App; Läufe "
                                   "anderer Apps bleiben unangetastet.")
visible = ids if app_filter == "(alle Apps)" else [
    r for r in ids if _parsed[r][1] == app_filter]
if not visible:
    st.info("Keine Läufe für diese App.")
    st.stop()

default_id = st.session_state.get("last_record_id", visible[0])
default_idx = visible.index(default_id) if default_id in visible else 0
with scol:
    record_id = st.selectbox(
        "Experiment (Lauf)", visible, index=default_idx,
        format_func=lambda r: f"{_parsed[r][1]} · {_fmt_ts(_parsed[r][0])} · …{r[-6:]}")

dc1, dc2 = st.columns([1, 3])
with dc1:
    if st.button("Experiment löschen", help="Löscht NUR diesen einen Ergebnis-Datensatz."):
        store.delete(record_id)
        st.session_state.pop("last_record_id", None)
        st.rerun()

record = store.load(record_id)

# Prominenter App-Marker, damit sofort klar ist, zu welcher App dieser Lauf gehört.
st.markdown(f"### 🎯 Ziel-App: {record.app_name}")
st.caption(
    f"Lauf `{record.id}` · Provider `{record.provider}` · Modell `{record.model}` · "
    f"{record.created_at}"
)

# getattr: tolerate a running server that still has the pre-`evaluated` model
# cached (Streamlit re-runs pages, but keeps imported modules loaded).
record_evaluated = getattr(record, "evaluated", True)
if not record_evaluated:
    st.warning(
        "Dieser Lauf wurde **ohne Bewertung** gestartet (Checkbox „Bewerten (Runner + "
        "DeepEval)“ war deaktiviert): Die Skripte wurden nur generiert, nie ausgeführt "
        "oder gejudged. Ausführungs-/Judge-/ISO-Metriken sind daher leer — das ist kein "
        "Fehlschlag der Pipelines. Für Metriken den Lauf mit aktivierter Bewertung "
        "wiederholen.")

# --- export (so the full result can be downloaded instead of copied) ------- #
from tcgen.orchestration.report import record_to_markdown  # noqa: E402

_md = record_to_markdown(record)
ex1, ex2, _sp = st.columns([1, 1, 3])
with ex1:
    st.download_button("Export (Markdown)", data=_md,
                       file_name=f"ergebnis_{record.id}.md", mime="text/markdown",
                       help="Kompletter Bericht inkl. Tabelle, Judge-Begründungen, "
                            "Fehlern und Skripten — zum Weitergeben.")
with ex2:
    st.download_button("Export (JSON)", data=record.model_dump_json(indent=2),
                       file_name=f"ergebnis_{record.id}.json", mime="application/json",
                       help="Roher Experiment-Datensatz (maschinenlesbar).")

results = record.pipelines
rows = [flatten_result(r) for r in results]
labels = [r["script"] for r in rows]
std_by_label = {r.script.pipeline.script_label: r.metric_std for r in results}
max_runs = max((r.n_runs for r in results), default=1)
if max_runs > 1:
    st.caption(f"Wiederholungen pro LLM-Pipeline: {max_runs} — Werte sind "
               f"Mittelwerte, „± x“ ist die Standardabweichung.")

# --- summary metric cards -------------------------------------------------- #
st.markdown("### Überblick")
cols = st.columns(max(len(rows), 1))
for col, row, result in zip(cols, rows, results):
    with col:
        st.markdown(f"**{row['script']}**  \n`{row['pipeline']}` · {result.n_runs}×")
        if record_evaluated:
            # Functional Suitability per ISO/IEC 25023: sub-characteristics
            # only, no combined score (see Iso25010 docstring).
            st.metric("ISO Correctness", ui.fmt(row["iso_correctness"]))
            st.metric("ISO Completeness", ui.fmt(row["iso_completeness"]))
            st.metric("ISO Appropriateness", ui.fmt(row["iso_appropriateness"]))
            st.metric("Ausführbar / grün",
                      f"{ui.fmt(row['executed'])} / {ui.fmt(row['passed'])}")
            st.metric("SSR", ui.fmt(row["ssr"]))
        else:
            st.metric("Status", "nicht bewertet")
            st.caption("Nur Generierung — keine Ausführungs-/Judge-Metriken.")
        if row["error"]:
            st.error(row["error"], icon=None)


def _cell(value, key, label_key) -> str:
    s = std_by_label.get(label_key, {}).get(key)
    base = ui.fmt(value)
    if s and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{base} ± {s:.3f}"
    return base


# --- comparison table (metric x pipeline) ---------------------------------- #
st.markdown("### Vergleichstabelle — Metrik × Pipeline")
arrow = {True: " ↑", False: " ↓", None: ""}
table: dict[str, dict[str, str]] = {}
for key, label, higher in METRIC_COLUMNS:
    metric_label = label + arrow[higher]
    table[metric_label] = {row["script"]: _cell(row.get(key), key, row["script"])
                           for row in rows}
df = pd.DataFrame(table).T
df = df[labels] if all(c in df.columns for c in labels) else df
st.dataframe(df, use_container_width=True)
st.caption("↑ = höher ist besser, ↓ = niedriger ist besser. „n/a“ = für diese "
           "Pipeline nicht anwendbar (z. B. Hallucination beim Crawler). "
           "„± x“ = Standardabweichung über die Wiederholungen.")

# --- anomalies ------------------------------------------------------------- #
anomaly_results = [r for r in results if r.anomalies]
if anomaly_results:
    st.markdown("### Auffälligkeiten (über die Wiederholungen)")
    for r in anomaly_results:
        st.markdown(f"**{r.script.pipeline.script_label}**")
        for a in r.anomalies:
            st.markdown(f"- {a}")

# --- ISO breakdown chart --------------------------------------------------- #
st.markdown("### ISO/IEC 25010 — Functional Suitability")
st.caption("Gemessen nach ISO/IEC 25023 auf Subcharakteristik-Ebene — der "
           "Standard definiert bewusst keinen kombinierten Gesamtwert.")
iso_long = []
for row in rows:
    for sub, key in [
        ("Correctness", "iso_correctness"),
        ("Completeness", "iso_completeness"),
        ("Appropriateness", "iso_appropriateness"),
    ]:
        iso_long.append({"Pipeline": row["script"], "Subcharakteristik": sub,
                         "Score": row.get(key)})
iso_df = pd.DataFrame(iso_long)
if iso_df["Score"].notna().any():
    fig = px.bar(iso_df, x="Subcharakteristik", y="Score", color="Pipeline",
                 barmode="group", range_y=[0, 1],
                 color_discrete_sequence=ui.CHART_SEQUENCE)
    fig.update_layout(legend_title="", plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", height=380,
                      margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Keine ISO-Werte (Bewertung war deaktiviert oder Judge nicht verfügbar).")

# --- judge metrics chart --------------------------------------------------- #
st.markdown("### DeepEval — semantische Metriken")
judge_long = []
for row in rows:
    for label, key in [("Correctness", "correctness"),
                       ("Appropriateness", "appropriateness"),
                       ("Hallucination", "hallucination"),
                       ("Readability", "readability")]:
        judge_long.append({"Pipeline": row["script"], "Metrik": label,
                           "Score": row.get(key)})
judge_df = pd.DataFrame(judge_long)
if judge_df["Score"].notna().any():
    figj = px.bar(judge_df, x="Metrik", y="Score", color="Pipeline",
                  barmode="group", range_y=[0, 1],
                  color_discrete_sequence=ui.CHART_SEQUENCE)
    figj.update_layout(legend_title="", plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)", height=380,
                       margin=dict(t=10, b=10))
    st.plotly_chart(figj, use_container_width=True)
else:
    st.caption("Keine Judge-Werte verfügbar.")

# --- per-pipeline detail --------------------------------------------------- #
st.markdown("### Detail je Pipeline")
for result, row in zip(results, rows):
    with st.expander(f"{row['script']} — {row['pipeline']}"):
        meta = result.script.meta
        st.write(f"Generierungszeit: {ui.fmt(result.script.generation_time_s)} s · "
                 f"Modell: `{result.script.model}` · Provider: `{result.script.provider}`")
        if result.execution.first_error:
            st.error(f"Erster Test-Fehler: {result.execution.first_error}", icon=None)
        if meta:
            st.json(meta, expanded=False)
        if result.judge.reasons:
            st.markdown("**Judge-Begründungen**")
            for k, v in result.judge.reasons.items():
                st.markdown(f"- *{k}*: {v}")
        if result.execution.stdout:
            st.markdown("**pytest stdout (Ausschnitt)**")
            st.code(result.execution.stdout[-2000:], language="text")
        if result.execution.stderr:
            st.markdown("**stderr (Ausschnitt)**")
            st.code(result.execution.stderr[-1500:], language="text")
