"""Configure and run an experiment as a background job, with a live monitor."""

from __future__ import annotations

import ui_helpers as ui

ui.setup_page("Experiment starten")
ui.sidebar_status()

import streamlit as st  # noqa: E402

from config.settings import list_targets, load_target  # noqa: E402
from tcgen.jobs import JobManager  # noqa: E402
from tcgen.orchestration.models import Pipeline  # noqa: E402

mgr = JobManager()
store = mgr.store

ui.header(
    "Experiment starten",
    "Der Lauf startet als Hintergrund-Job und läuft weiter, auch wenn du den "
    "Tab wechselst oder die Seite verlässt. Der Monitor unten zeigt Fortschritt "
    "und Logs live.",
)

targets = list_targets()
if not targets:
    st.error("Keine Ziel-Definitionen unter config/targets/ gefunden.")
    st.stop()

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
col_a, col_b = st.columns([1, 1])
with col_a:
    app_key = st.selectbox("Ziel-Anwendung", targets, index=0)
    target = load_target(app_key)
    st.caption(target.description.strip() or target.base_url)
    st.write(f"**Base-URL:** `{target.base_url}`")

with col_b:
    pipeline_labels = {
        "Crawler — Skript_C (Methode 1)": Pipeline.CRAWLER,
        "LLM-Agent — Skript_L (Methode 1)": Pipeline.LLM_AGENT,
    }
    chosen = st.multiselect(
        "Pipelines (Methode 1)",
        list(pipeline_labels.keys()),
        default=list(pipeline_labels.keys()),
    )
    include_hybrid = st.checkbox("Hybrid — Skript_H (Methode 2) zuschalten", value=False)
    evaluate = st.checkbox("Bewerten (Runner + DeepEval)", value=True,
                           help="Aus: nur Generierung, keine Ausführung/Bewertung.")

st.caption(
    "Methode 1: Der LLM-Agent bekommt dieselbe Aufgabe wie der Crawler "
    "(App autonom erkunden und Testsuite erzeugen); die User-Stories dienen als "
    "zusätzlicher Kontext zur Priorisierung."
)

domain_context = ""
if include_hybrid:
    domain_context = st.text_area(
        "Fachliche Zusatzinfos für den Hybrid-Refiner (optional)",
        placeholder="z. B. Domänenregeln, kritische Prüfpunkte, erwartete Fehlermeldungen …",
        height=100,
    )

with st.expander("User-Stories dieser Ziel-App"):
    for s in target.user_stories:
        st.markdown(f"**{s.id} — {s.title}**")
        st.write(s.text.strip())
        if s.acceptance_criteria:
            st.caption("Akzeptanzkriterien: " + "; ".join(s.acceptance_criteria))

pipelines = [pipeline_labels[c] for c in chosen]

st.markdown('<hr class="accent-rule">', unsafe_allow_html=True)
if st.button("Lauf starten", type="primary", disabled=not pipelines):
    job_id = mgr.start(
        app_key, pipelines,
        include_hybrid=include_hybrid, evaluate=evaluate, domain_context=domain_context,
    )
    st.session_state["active_job_id"] = job_id
    st.success(f"Job gestartet: `{job_id}`")
    st.rerun()

# --------------------------------------------------------------------------- #
# Live monitor + reattach
# --------------------------------------------------------------------------- #
st.markdown("## Live-Monitor")
jobs = mgr.list(limit=30)
if not jobs:
    st.caption("Noch keine Jobs gestartet.")
    st.stop()

job_ids = [j.id for j in jobs]
preselect = st.session_state.get("active_job_id")
idx = job_ids.index(preselect) if preselect in job_ids else 0
selected = st.selectbox("Job", job_ids, index=idx,
                        help="Laufende oder abgeschlossene Jobs lassen sich hier erneut öffnen.")
st.session_state["active_job_id"] = selected

# Poll only while the job is active; finished jobs render once.
_initial = store.load(selected)
_interval = 2 if _initial.is_active else None


@st.fragment(run_every=_interval)
def _monitor() -> None:
    job = store.load(selected)
    ui.render_job_monitor(job)
    if job.status == "done" and job.result_id:
        st.session_state["last_record_id"] = job.result_id
        st.success(f"Fertig. Ergebnis: `{job.result_id}`")
        st.page_link("pages/2_Ergebnisse.py", label="Zu den Ergebnissen")
    elif job.status == "error":
        st.error(job.error or "Unbekannter Fehler — siehe Logdatei im results/jobs-Ordner.")


_monitor()
