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
    SYNTHESIS_SYSTEM_STORY,
    explore_goal,
    repair_user_prompt,
    synthesis_user_prompt,
    synthesis_user_prompt_story,
)
from tcgen.util import (
    extract_code_block,
    extract_json_object,
    truncate,
    validate_playwright_code,
)

log = logging.getLogger(__name__)


def _as_str(value) -> str:
    """Coerce an arbitrary JSON value to a stripped string.

    Returns '' for None and for nested dicts/lists, so a malformed model reply
    (e.g. ``{"action": {...}}``) can never crash the exploration loop.
    """
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


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
    def generate(self, phase: Phase | None = None, *, with_stories: bool = False) -> GeneratedScript:
        phase = phase or NullPhase()
        t0 = time.time()
        pipeline = Pipeline.LLM_AGENT_STORY if with_stories else Pipeline.LLM_AGENT
        story_block = _story_block(self.target.user_stories) if with_stories else None
        mode = "mit User-Story" if with_stories else "ohne User-Story"
        phase.update(0.02, f"Agent startet Exploration (Crawler-Aufgabe, {mode})")
        with BrowserSession(
            self.target.base_url,
            headless=self.settings.headless,
            settle_timeout_ms=self.settings.settle_timeout_ms,
            settle_pause_ms=self.settings.settle_pause_ms,
        ) as session:
            observation = session.navigate(self.target.entry_paths[0])
            action_log, pages = self._explore(session, observation, phase, story_block)
        phase.update(0.9, "Synthese der Testsuite aus Beobachtungen")
        transcript = self._build_transcript(action_log, pages)
        code = self._synthesize(transcript, story_block)
        code = self._maybe_repair(code, phase)
        phase.update(1.0, f"{pipeline.script_label} erzeugt ({len(code.splitlines())} Zeilen)")
        return GeneratedScript(
            pipeline=pipeline,
            app_key=self.target.key,
            language="python",
            code=code,
            generation_time_s=round(time.time() - t0, 2),
            model=self.provider.model,
            provider=self.provider.name,
            meta={
                "agent_steps": len(action_log),
                "pages_observed": len(pages),
                "user_story_used": with_stories,
            },
        )

    # ------------------------------------------------------------------ #
    def _explore(self, session: BrowserSession, observation, phase: Phase,
                 story_block: str | None = None):
        action_log: list[str] = []
        pages: dict[str, str] = {}  # url -> digest (deduplicated)
        max_steps = self.settings.agent_max_steps
        goal = explore_goal(story_block)

        for step in range(max_steps):
            pages.setdefault(session.page.url, observation)
            phase.update(0.02 + 0.86 * (step / max_steps),
                         f"Agent: Schritt {step + 1}/{max_steps} · {session.page.url}")
            user = (
                f"GOAL: {goal}\n\n"
                f"ACTION LOG SO FAR:\n" + ("\n".join(action_log) or "(none)") + "\n\n"
                f"CURRENT OBSERVATION:\n{observation}\n\n"
                "Reply with the next action as a single JSON object."
            )
            messages: list[Message] = [
                {"role": "system", "content": EXPLORE_SYSTEM},
                {"role": "user", "content": user},
            ]
            reply = self.provider.chat(messages, json_mode=True)
            # Defensive parsing: small local models sometimes return non-objects
            # or nest values, so coerce every field to a plain string.
            raw = extract_json_object(reply)
            if not isinstance(raw, dict):
                raw = {}
            kind = _as_str(raw.get("action")).lower()
            ref, url, value = _as_str(raw.get("ref")), _as_str(raw.get("url")), _as_str(raw.get("value"))
            log.debug("agent step %d: %s", step, raw)
            phase.log(f"  Aktion: {kind} {ref}{url}{(' = ' + value) if kind == 'fill' else ''}".rstrip())

            if not kind or kind == "finish":
                action_log.append(f"{step}: finish")
                break
            try:
                observation = self._dispatch(session, kind, ref, url, value)
                action_log.append(f"{step}: {kind} {ref}{url}"
                                   f"{(' = ' + value) if kind == 'fill' else ''}")
            except Exception as exc:  # noqa: BLE001
                observation = f"ERROR executing {kind}: {exc}\n\n{session.observe()}"
                action_log.append(f"{step}: {kind} -> ERROR: {exc}")
        return action_log, pages

    def _dispatch(self, session: BrowserSession, kind: str, ref: str, url: str, value: str) -> str:
        if kind == "navigate":
            return session.navigate(url or "/")
        if kind == "click":
            return session.click(ref)
        if kind == "fill":
            return session.fill(ref, value)
        if kind == "get_text":
            return "PAGE TEXT:\n" + session.get_text() + "\n\n" + session.observe()
        raise ValueError(f"Unknown action {kind!r}")

    def _build_transcript(self, action_log: list[str], pages: dict[str, str]) -> str:
        parts = ["ACTION LOG:", "\n".join(action_log), "", "PAGES OBSERVED:"]
        for url, digest in pages.items():
            parts.append(f"\n--- {url} ---\n{truncate(digest, 1200)}")
        return truncate("\n".join(parts), 6000)

    def _synthesize(self, transcript: str, story_block: str | None = None) -> str:
        if story_block:
            system = SYNTHESIS_SYSTEM_STORY
            user = synthesis_user_prompt_story(self.target.base_url, story_block, transcript)
        else:
            system = SYNTHESIS_SYSTEM
            user = synthesis_user_prompt(self.target.base_url, transcript)
        messages: list[Message] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
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
             phase=None, *, with_stories: bool = False) -> GeneratedScript:
    return LLMAgent(target, settings).generate(phase=phase, with_stories=with_stories)
