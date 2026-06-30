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
        "Crawler — Skript_C": Pipeline.CRAWLER,
        "LLM-Agent — Skript_L (ohne Story)": Pipeline.LLM_AGENT,
        "LLM-Agent + User-Story — Skript_S": Pipeline.LLM_AGENT_STORY,
    }
    chosen = st.multiselect(
        "Pipelines",
        list(pipeline_labels.keys()),
        default=list(pipeline_labels.keys()),
        help="Skript_S = LLM-Agent, der die App erkundet UND die User-Stories bekommt.",
    )
    include_hybrid = st.checkbox("Hybrid — Skript_H (Methode 2) zuschalten", value=True)
    reuse_crawler = st.checkbox(
        "Crawler nicht neu laufen lassen (letzten Skript_C wiederverwenden)",
        value=True,
        help="Überspringt die langsame Crawler-Exploration und nutzt den zuletzt "
             "für diese App erzeugten Skript_C aus results/. Praktisch, wenn die "
             "Baseline schon steht und nur die LLM-Pipelines neu laufen sollen.",
    )
    evaluate = st.checkbox("Bewerten (Runner + DeepEval)", value=True,
                           help="Aus: nur Generierung, keine Ausführung/Bewertung.")

st.caption(
    "Methode 1 (Crawler, LLM-Agent) ist anforderungsfrei: beide erkunden die App "
    "autonom. Die gewählten User-Stories steuern nur den Hybrid-Refiner (Methode 2) "
    "und die story-bewusste Bewertung von Skript_H."
)

# --- user-story filter (scopes Hybrid + judge) ---
story_options = {f"{s.id} — {s.title}": s.id for s in target.user_stories}
chosen_stories = st.multiselect(
    "User-Stories (steuern Hybrid + Bewertung)",
    list(story_options.keys()),
    default=list(story_options.keys()),
    help="Auswahl der Akzeptanzkriterien, gegen die Skript_H verfeinert/bewertet wird.",
)
user_story_ids = [story_options[s] for s in chosen_stories]

col_r, col_d = st.columns([1, 2])
with col_r:
    repetitions = st.number_input(
        "Wiederholungen (LLM + Judge)", min_value=1, max_value=100, value=1, step=1,
        help="LLM-Stufen und Judge werden N× ausgeführt und zu Mittelwert ± Std "
             "kumuliert. Der Crawler wird einmal generiert.",
    )
domain_context = ""
if include_hybrid:
    with col_d:
        domain_context = st.text_area(
            "Fachliche Zusatzinfos für den Hybrid-Refiner (optional)",
            placeholder="z. B. Domänenregeln, kritische Prüfpunkte, erwartete Fehlermeldungen …",
            height=100,
        )

with st.expander("Akzeptanzkriterien der gewählten User-Stories"):
    for s in target.user_stories:
        if s.id not in user_story_ids:
            continue
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
        user_story_ids=user_story_ids, repetitions=int(repetitions),
        reuse_crawler=reuse_crawler,
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

# --- controls (outside the auto-refresh fragment) ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    if st.button("Abbrechen", disabled=not _initial.is_active,
                 help="Bricht den laufenden Worker (inkl. Browser) ab."):
        mgr.cancel(selected)
        st.rerun()
with c2:
    if st.button("Job löschen"):
        mgr.delete(selected)
        st.session_state.pop("active_job_id", None)
        st.rerun()
with c3:
    if st.button("Abgeschlossene Jobs aufräumen",
                 help="Löscht alle nicht-laufenden Jobs (fertig/Fehler/abgebrochen)."):
        n = mgr.cleanup_finished()
        st.session_state.pop("active_job_id", None)
        st.toast(f"{n} Job(s) gelöscht")
        st.rerun()


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
