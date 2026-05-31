"""LLM agent: explore a live app autonomously (no user story), then synthesise
Skript_L. The agent's task is identical to the crawler's — requirement knowledge
enters only in Methode 2 (the hybrid refiner). ``_story_block`` is kept here and
reused by the refiner/experiment for the story-aware Skript_H path."""

from __future__ import annotations

import logging
import time

from config.settings import Settings, TargetApp, UserStory, get_settings
from tcgen.llm import LLMProvider, Message, get_provider
from tcgen.orchestration.models import GeneratedScript, Pipeline
from tcgen.progress import NullPhase, Phase
from tcgen.pipelines.llm_agent.browser_tools import BrowserSession
from tcgen.pipelines.llm_agent.prompts import (
    EXPLORE_SYSTEM,
    REPAIR_SYSTEM,
    SYNTHESIS_SYSTEM,
    repair_user_prompt,
    synthesis_user_prompt,
)
from tcgen.util import (
    extract_code_block,
    extract_json_object,
    truncate,
    validate_playwright_code,
)

log = logging.getLogger(__name__)


def _story_block(stories: list[UserStory]) -> str:
    out = []
    for s in stories:
        crit = "\n".join(f"    - {c}" for c in s.acceptance_criteria)
        out.append(f"{s.id} — {s.title}\n  {s.text.strip()}\n  Acceptance:\n{crit}")
    return "\n\n".join(out)


class LLMAgent:
    def __init__(self, target: TargetApp, settings: Settings | None = None,
                 provider: LLMProvider | None = None):
        self.target = target
        self.settings = settings or get_settings()
        self.provider = provider or get_provider(self.settings)

    # ------------------------------------------------------------------ #
    def generate(self, phase: Phase | None = None) -> GeneratedScript:
        phase = phase or NullPhase()
        t0 = time.time()
        phase.update(0.02, "Agent startet Exploration (Crawler-Aufgabe, ohne User-Story)")
        with BrowserSession(
            self.target.base_url,
            headless=self.settings.headless,
            settle_timeout_ms=self.settings.settle_timeout_ms,
            settle_pause_ms=self.settings.settle_pause_ms,
        ) as session:
            observation = session.navigate(self.target.entry_paths[0])
            action_log, pages = self._explore(session, observation, phase)
        phase.update(0.9, "Synthese der Testsuite aus Beobachtungen")
        transcript = self._build_transcript(action_log, pages)
        code = self._synthesize(transcript)
        code = self._maybe_repair(code, phase)
        phase.update(1.0, f"Skript_L erzeugt ({len(code.splitlines())} Zeilen)")
        return GeneratedScript(
            pipeline=Pipeline.LLM_AGENT,
            app_key=self.target.key,
            language="python",
            code=code,
            generation_time_s=round(time.time() - t0, 2),
            model=self.provider.model,
            provider=self.provider.name,
            meta={
                "agent_steps": len(action_log),
                "pages_observed": len(pages),
                "user_story_used": False,
            },
        )

    # ------------------------------------------------------------------ #
    def _explore(self, session: BrowserSession, observation, phase: Phase):
        action_log: list[str] = []
        pages: dict[str, str] = {}  # url -> digest (deduplicated)
        max_steps = self.settings.agent_max_steps

        for step in range(max_steps):
            pages.setdefault(session.page.url, observation)
            phase.update(0.02 + 0.86 * (step / max_steps),
                         f"Agent: Schritt {step + 1}/{max_steps} · {session.page.url}")
            user = (
                "GOAL: explore the application broadly to map its main "
                "user-facing flows (navigation, search, forms, detail views).\n\n"
                f"ACTION LOG SO FAR:\n" + ("\n".join(action_log) or "(none)") + "\n\n"
                f"CURRENT OBSERVATION:\n{observation}\n\n"
                "Reply with the next action as a single JSON object."
            )
            messages: list[Message] = [
                {"role": "system", "content": EXPLORE_SYSTEM},
                {"role": "user", "content": user},
            ]
            reply = self.provider.chat(messages, json_mode=True)
            action = extract_json_object(reply)
            kind = (action.get("action") or "").strip().lower()
            log.debug("agent step %d: %s", step, action)
            phase.log(f"  Aktion: {kind} {action.get('ref', '')}{action.get('url', '')}"
                      f"{(' = ' + action.get('value', '')) if kind == 'fill' else ''}".rstrip())

            if not kind or kind == "finish":
                action_log.append(f"{step}: finish")
                break
            try:
                observation = self._dispatch(session, kind, action)
                action_log.append(f"{step}: {kind} {action.get('ref','')}{action.get('url','')}"
                                   f"{(' = ' + action.get('value','')) if kind=='fill' else ''}")
            except Exception as exc:  # noqa: BLE001
                observation = f"ERROR executing {kind}: {exc}\n\n{session.observe()}"
                action_log.append(f"{step}: {kind} -> ERROR: {exc}")
        return action_log, pages

    def _dispatch(self, session: BrowserSession, kind: str, action: dict) -> str:
        if kind == "navigate":
            return session.navigate(action.get("url", "/"))
        if kind == "click":
            return session.click(action["ref"])
        if kind == "fill":
            return session.fill(action["ref"], action.get("value", ""))
        if kind == "get_text":
            return "PAGE TEXT:\n" + session.get_text() + "\n\n" + session.observe()
        raise ValueError(f"Unknown action {kind!r}")

    def _build_transcript(self, action_log: list[str], pages: dict[str, str]) -> str:
        parts = ["ACTION LOG:", "\n".join(action_log), "", "PAGES OBSERVED:"]
        for url, digest in pages.items():
            parts.append(f"\n--- {url} ---\n{truncate(digest, 1200)}")
        return truncate("\n".join(parts), 6000)

    def _synthesize(self, transcript: str) -> str:
        messages: list[Message] = [
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": synthesis_user_prompt(
                self.target.base_url, transcript)},
        ]
        reply = self.provider.chat(messages)
        return extract_code_block(reply)

    def _maybe_repair(self, code: str, phase: Phase) -> str:
        """One validate+repair round so Skript_L is at least runnable Python."""
        if not self.settings.agent_repair:
            return code
        issues = validate_playwright_code(code)
        if not issues:
            return code
        phase.log("Validierung fand Probleme: " + "; ".join(issues) + " — Repair-Runde")
        messages: list[Message] = [
            {"role": "system", "content": REPAIR_SYSTEM},
            {"role": "user", "content": repair_user_prompt(code, issues)},
        ]
        try:
            repaired = extract_code_block(self.provider.chat(messages))
        except Exception as exc:  # noqa: BLE001
            phase.log(f"Repair fehlgeschlagen ({exc}) — behalte Originalskript")
            return code
        remaining = validate_playwright_code(repaired)
        if remaining and len(remaining) >= len(issues):
            phase.log("Repair brachte keine Verbesserung — behalte Originalskript")
            return code
        phase.log(f"Repair angewandt: {len(issues)} -> {len(remaining)} Probleme")
        return repaired


def generate(target: TargetApp, settings: Settings | None = None,
             phase=None) -> GeneratedScript:
    return LLMAgent(target, settings).generate(phase=phase)
