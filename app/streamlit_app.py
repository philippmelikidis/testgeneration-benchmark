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

c1, c2, c3 = st.columns(3)
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
        "LLM-Agent bekommt dieselbe Aufgabe wie der Crawler: die App über ein "
        "JSON-Aktionsprotokoll autonom erkunden und eine Testsuite erzeugen. "
        "User-Stories dienen als zusätzlicher Kontext zur Priorisierung."
    )
with c3:
    st.markdown("### Skript_H — Hybrid")
    st.caption("Methode 2, Aufsatz")
    st.write(
        "LLM-Refiner nimmt Skript_C als Eingabe und verbessert es entlang dreier "
        "Achsen: robuste Locator, fehlende Assertions, Lesbarkeit. Drei-Wege-Vergleich."
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
