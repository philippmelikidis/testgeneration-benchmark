"""LLM agent: explore a live app from user stories, then synthesise Skript_L."""

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
    SYNTHESIS_SYSTEM,
    synthesis_user_prompt,
)
from tcgen.util import extract_code_block, extract_json_object, truncate

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
        stories = self.target.user_stories
        phase.update(0.02, "Agent startet Exploration (Crawler-Aufgabe, Stories als Kontext)")
        with BrowserSession(
            self.target.base_url,
            headless=self.settings.headless,
            settle_timeout_ms=self.settings.settle_timeout_ms,
            settle_pause_ms=self.settings.settle_pause_ms,
        ) as session:
            observation = session.navigate(self.target.entry_paths[0])
            action_log, pages = self._explore(session, stories, observation, phase)
        phase.update(0.9, "Synthese der Testsuite aus Beobachtungen")
        transcript = self._build_transcript(action_log, pages)
        code = self._synthesize(stories, transcript)
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
                "user_stories": [s.id for s in stories],
            },
        )

    # ------------------------------------------------------------------ #
    def _explore(self, session: BrowserSession, stories, observation, phase: Phase):
        goals = _story_block(stories)
        action_log: list[str] = []
        pages: dict[str, str] = {}  # url -> digest (deduplicated)
        max_steps = self.settings.agent_max_steps

        for step in range(max_steps):
            pages.setdefault(session.page.url, observation)
            phase.update(0.02 + 0.86 * (step / max_steps),
                         f"Agent: Schritt {step + 1}/{max_steps} · {session.page.url}")
            user = (
                f"GOALS (user stories to test):\n{goals}\n\n"
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

    def _synthesize(self, stories, transcript: str) -> str:
        messages: list[Message] = [
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": synthesis_user_prompt(
                self.target.base_url, _story_block(stories), transcript)},
        ]
        reply = self.provider.chat(messages)
        return extract_code_block(reply)


def generate(target: TargetApp, settings: Settings | None = None,
             phase=None) -> GeneratedScript:
    return LLMAgent(target, settings).generate(phase=phase)
