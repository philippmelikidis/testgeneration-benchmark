"""Shared helpers for the Streamlit UI: path bootstrap, theme CSS, formatting.

Imported by the entry script and every page. Importing this module ensures the
project root is on ``sys.path`` so ``tcgen`` and ``config`` resolve regardless of
how Streamlit launches the page.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- project-root bootstrap (must run before importing tcgen/config) ---------
_ROOT = Path(__file__).resolve()
while _ROOT != _ROOT.parent and not (_ROOT / "tcgen").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

ACCENT = "#3b6ea5"
GOOD = "#2f8f5b"
BAD = "#b3433b"
# Calm, colourblind-friendly, distinct — no navy/orange.
PIPELINE_COLORS = {
    "crawler": "#3b6ea5",     # Skript_C — muted blue
    "llm_agent": "#5a9e9f",   # Skript_L — teal
    "hybrid": "#8a6fae",      # Skript_H — muted violet
}
CHART_SEQUENCE = ["#3b6ea5", "#5a9e9f", "#8a6fae"]

_CSS = """
<style>
  .block-container { padding-top: 2.2rem; max-width: 1200px; }
  h1, h2, h3 { letter-spacing: .2px; color: #1f2933; }
  h1 { font-weight: 700; }
  h2 { border-bottom: 2px solid #3b6ea533; padding-bottom: .3rem; }
  .accent-rule { height: 3px; width: 64px; background: #3b6ea5; border: none;
                 margin: .2rem 0 1.2rem 0; }
  .lead { color: #5b6571; font-size: 1.02rem; line-height: 1.5; }
  div[data-testid="stMetric"] { background: #f6f8fa; border: 1px solid #dde1e6;
        border-radius: 8px; padding: .8rem 1rem; }
  div[data-testid="stMetricLabel"] { color: #5b6571; }
  .stDataFrame { border: 1px solid #dde1e6; border-radius: 8px; }
  .pill { display:inline-block; padding:.15rem .6rem; border-radius:999px;
          font-size:.78rem; font-weight:600; margin-right:.4rem; }
</style>
"""


def setup_page(title: str, *, icon: str | None = None) -> None:
    st.set_page_config(page_title=f"{title} · TCGen Benchmark",
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f'<p class="lead">{subtitle}</p>', unsafe_allow_html=True)


def sidebar_status() -> None:
    """Show the active provider/model and run parameters."""
    from config.settings import get_settings

    s = get_settings()
    with st.sidebar:
        st.markdown("### Konfiguration")
        st.write(f"**Provider:** `{s.llm_provider}`")
        st.write(f"**Generierungs-Modell:** `{s.generation_model}`")
        st.write(f"**Judge-Modell:** `{s.judge_model}`")
        st.caption(
            f"headless={s.headless} · flakiness_runs={s.flakiness_runs} · "
            f"agent_max_steps={s.agent_max_steps} · crawler_max_states={s.crawler_max_states}"
        )
        st.caption("Anpassbar über .env (Präfix TCGEN_).")

        from tcgen.util import same_model_family

        if same_model_family(s.generation_model, s.judge_model):
            st.warning(
                "Generator und Judge sind dieselbe Modellfamilie — möglicher "
                "LLM-Judge-Bias. Für belastbare Zahlen einen Judge aus einer "
                "anderen Familie wählen (z. B. llama3.1:8b).",
                icon=None,
            )


_STATUS_LABEL = {"pending": "wartet", "running": "läuft", "done": "fertig",
                 "error": "Fehler", "cancelled": "abgebrochen"}
_STATUS_COLOR = {"pending": "#7a869a", "running": "#3b6ea5", "done": "#2f8f5b",
                 "error": "#b3433b", "cancelled": "#8a6fae"}


def render_job_monitor(job, *, log_lines: int = 40) -> None:
    """Render a job's status badge, progress bar, and tail of its log stream."""
    color = _STATUS_COLOR.get(job.status, "#7a869a")
    label = _STATUS_LABEL.get(job.status, job.status)
    st.markdown(
        f'<span class="pill" style="background:{color};color:#fff">{label}</span>'
        f'<span style="color:#5b6571">&nbsp;{job.message}</span>',
        unsafe_allow_html=True,
    )
    st.progress(min(max(job.percent, 0.0), 1.0), text=f"{job.percent * 100:.0f}%")
    st.code("\n".join(job.logs[-log_lines:]) or "(noch keine Logs)", language="text")


def fmt(v, digits: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)
