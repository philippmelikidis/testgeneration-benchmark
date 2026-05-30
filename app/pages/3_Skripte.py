"""Inspect the generated test scripts side by side."""

from __future__ import annotations

import ui_helpers as ui

ui.setup_page("Skripte")
ui.sidebar_status()

import streamlit as st  # noqa: E402

from tcgen.orchestration.results_store import ResultsStore  # noqa: E402

ui.header("Generierte Skripte", "Die Artefakte jeder Pipeline im Vergleich.")

store = ResultsStore()
ids = store.list_ids()
if not ids:
    st.info("Noch keine Experimente vorhanden.")
    st.stop()

default_id = st.session_state.get("last_record_id", ids[0])
default_idx = ids.index(default_id) if default_id in ids else 0
record_id = st.selectbox("Experiment", ids, index=default_idx)
record = store.load(record_id)

results = [r for r in record.pipelines if r.script.code]
if not results:
    st.warning("Dieses Experiment enthält keine Skript-Artefakte.")
    st.stop()

tabs = st.tabs([r.script.pipeline.script_label for r in results])
for tab, result in zip(tabs, results):
    with tab:
        s = result.script
        st.caption(
            f"{s.pipeline.value} · Modell `{s.model}` · "
            f"Generierungszeit {ui.fmt(s.generation_time_s)} s · "
            f"{len(s.code.splitlines())} Zeilen"
        )
        st.code(s.code or "# (leer)", language="python")
        st.download_button(
            "Skript herunterladen",
            data=s.code,
            file_name=f"{s.pipeline.script_label}_{record.app_key}.py",
            mime="text/x-python",
        )
