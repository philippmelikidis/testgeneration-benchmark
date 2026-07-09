"""Skript_H (Methode 2) — GROUNDED AGENT.

Earlier iterations generated Skript_H in a single blind LLM call from the crawler
catalog ("refine"). That capped H at what the crawler happened to catalogue and
produced hollow assertions for anything the crawler never reached (login,
register). Skript_H is now a LIVE agent instead: it reuses the proven
explore→synthesise loop of :class:`LLMAgent`, but is SEEDED with the crawler's
state graph — its discovered ``routes`` and verified ``locator_catalog`` — as
grounding. So it clicks through the app itself (verifying elements against the
live DOM, reaching login/register on its own), while the crawler map keeps it
on-task and anchored to real selectors. Output pipeline stays HYBRID.
"""

from __future__ import annotations

from config.settings import Settings, TargetApp, get_settings
from tcgen.orchestration.models import GeneratedScript, Pipeline
from tcgen.pipelines.llm_agent.agent import LLMAgent


def generate(script_c: GeneratedScript, target: TargetApp,
             settings: Settings | None = None, *, domain_context: str = "",
             phase=None) -> GeneratedScript:
    """Run the grounded agent for Skript_H, seeded with the crawler map."""
    settings = settings or get_settings()
    grounding = {
        "routes": script_c.meta.get("routes") or [],
        "catalog": script_c.meta.get("locator_catalog") or [],
    }
    agent = LLMAgent(target, settings, grounding=grounding)
    script = agent.generate(phase=phase, with_stories=True,
                            pipeline_override=Pipeline.HYBRID)
    # Methode 2's generation cost includes the crawl it depends on.
    crawl_time = float(script_c.meta.get("crawl_time_s") or 0.0)
    script.generation_time_s = round(script.generation_time_s + crawl_time, 2)
    script.meta.update({
        "refined_from": Pipeline.CRAWLER.value,
        "exploration_time_s": crawl_time,
        "input_element_coverage": script_c.meta.get("element_coverage"),
        "domain_context_used": bool(domain_context.strip()),
    })
    return script


class HybridRefiner:
    """Backward-compatible thin wrapper around :func:`generate`."""

    def __init__(self, target: TargetApp, settings: Settings | None = None):
        self.target = target
        self.settings = settings or get_settings()

    def refine(self, script_c: GeneratedScript, *, domain_context: str = "",
               phase=None) -> GeneratedScript:
        return generate(script_c, self.target, self.settings,
                        domain_context=domain_context, phase=phase)
