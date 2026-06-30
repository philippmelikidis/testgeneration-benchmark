"""TCGen Benchmark — entry page.

Run with:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import ui_helpers as ui

ui.setup_page("Übersicht")
ui.sidebar_status()

import streamlit as st  # noqa: E402

st.markdown("# LLM vs. traditionelle Web-UI-Testfallgenerierung")
st.markdown('<hr class="accent-rule">', unsafe_allow_html=True)
st.markdown(
    '<p class="lead">Empirische Werkbank zum Methodenentwurf: drei Generierungs-'
    "Pipelines auf denselben User-Stories und Ziel-Anwendungen, bewertet durch "
    "eine gemeinsame Metrik-Suite (objektiv + DeepEval) und auf ISO/IEC 25010 "
    "Functional Suitability abgebildet.</p>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("### Skript_C — Crawler")
    st.caption("Methode 1, traditionell")
    st.write(
        "Autonomer Playwright-Crawler erkundet die App, baut einen Zustandsgraphen "
        "aus DOM-Übergängen und serialisiert Pfade zu einem pytest-Skript. "
        "Keine User-Story im Spiel."
    )
with c2:
    st.markdown("### Skript_L — LLM-Agent")
    st.caption("Methode 1, LLM-only")
    st.write(
        "LLM-Agent bekommt dieselbe Aufgabe wie der Crawler: die App autonom über "
        "den Playwright-MCP-Server erkunden und eine Testsuite erzeugen. "
        "**Ohne** User-Story."
    )
with c3:
    st.markdown("### Skript_S — LLM-Agent + Story")
    st.caption("LLM-only, story-bewusst")
    st.write(
        "Wie Skript_L, aber der Agent bekommt zusätzlich die User-Stories und "
        "erkundet die App, um genau diese Stories zu testen. Isoliert (vs. L) den "
        "Effekt der Anforderungen beim LLM-Agenten."
    )
with c4:
    st.markdown("### Skript_H — Hybrid")
    st.caption("Methode 2, geerdet")
    st.write(
        "LLM bekommt die Crawler-Map (entdeckte Routen + echte, verifizierte "
        "Locator) **plus** die User-Stories und schreibt damit grounded eine "
        "Story-Testsuite — nur reale Elemente, keine erfundenen Selektoren."
    )

st.markdown("## Vorgehen")
st.markdown(
    "1. **Experiment starten** — Ziel-App, Provider und Pipelines wählen, Lauf ausführen.\n"
    "2. **Ergebnisse** — Vergleichstabelle Pipeline × Metrik, ISO-Aufschlüsselung, Charts.\n"
    "3. **Skripte** — generierte Testskripte nebeneinander inspizieren."
)

st.info(
    "Methode 1 ist der lauffähige Kern (Crawler + LLM-Agent). Methode 2 (Hybrid) "
    "lässt sich pro Lauf zuschalten, ohne die Baseline zu verändern.",
    icon=None,
)

# Quick view of how many experiments are stored.
try:
    from tcgen.orchestration.results_store import ResultsStore

    n = len(ResultsStore().list_ids())
    st.caption(f"Gespeicherte Experimente: {n}")
except Exception as exc:  # noqa: BLE001
    st.caption(f"Results-Store nicht lesbar: {exc}")
