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

default_id = st.session_state.get("last_record_id", ids[0])
default_idx = ids.index(default_id) if default_id in ids else 0
record_id = st.selectbox("Experiment", ids, index=default_idx)

dc1, dc2 = st.columns([1, 3])
with dc1:
    if st.button("Experiment löschen", help="Löscht diesen Ergebnis-Datensatz."):
        store.delete(record_id)
        st.session_state.pop("last_record_id", None)
        st.rerun()

record = store.load(record_id)

st.markdown(
    f"**{record.app_name}** · Provider `{record.provider}` · Modell `{record.model}` · "
    f"{record.created_at}"
)

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
        st.metric("ISO Functional Suitability", ui.fmt(row["iso_overall"]))
        st.metric("Ausführbar / grün",
                  f"{ui.fmt(row['executed'])} / {ui.fmt(row['passed'])}")
        st.metric("SSR", ui.fmt(row["ssr"]))
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
st.caption("↑ = höher ist besser, ↓ = niedriger ist besser. „—“ = nicht verfügbar. "
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
