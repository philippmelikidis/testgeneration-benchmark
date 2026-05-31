"""LLM refiner: Skript_C -> Skript_H (Methode 2)."""

from __future__ import annotations

import time

from config.settings import Settings, TargetApp, get_settings
from tcgen.llm import LLMProvider, Message, get_provider
from tcgen.orchestration.models import GeneratedScript, Pipeline
from tcgen.pipelines.llm_agent.agent import _story_block
from tcgen.util import extract_code_block

REFINER_SYSTEM = """\
You are a senior test automation engineer performing a focused refactor of an
existing Playwright (pytest) test module that was produced by an autonomous
crawler. Improve the script along EXACTLY these three axes, and nothing else:

1. Robust locators: where the input uses a fragile selector, prefer a more
   robust user-facing locator BUILT FROM INFORMATION ALREADY IN THE INPUT (the
   element's visible text, role, or placeholder that appears there).
2. Oracles: add meaningful `expect(...)` assertions that tie each test to the
   relevant user story's acceptance criteria. Do not weaken existing assertions.
3. Readability and maintainability: clear test names, short comments where a step
   is non-obvious, no dead code.

GROUNDING — hard rules (the input crawler script is your only source of truth
about the application; you have NOT seen the live DOM):
- Reuse the navigation and the elements that the input script actually touches.
- Do NOT invent selectors for elements that do not appear in the input: no made-up
  CSS classes (e.g. `.product-card`), ids, placeholders, ARIA roles, or routes.
- If you cannot ground an assertion in something the input script already
  reaches, keep a conservative assertion (page reachable, body visible) instead
  of inventing app-specific selectors.

Constraints:
- Keep it a runnable pytest-playwright module using the `page: Page` fixture.
- Output ONLY the refactored Python code in a single ```python fenced block.
"""


def _user_prompt(base_url: str, story_block: str, script_c: str,
                 domain_context: str = "") -> str:
    domain = domain_context.strip()
    domain_section = (
        f"\nDOMAIN / EXPERT CONTEXT (use to make assertions more meaningful):\n{domain}\n"
        if domain else ""
    )
    return f"""\
BASE URL: {base_url}

USER STORIES (use these to add/strengthen assertions):
{story_block}
{domain_section}
INPUT SCRIPT (Skript_C, produced by an autonomous crawler):
```python
{script_c}
```

Return the improved module (Skript_H).
"""


class HybridRefiner:
    def __init__(self, target: TargetApp, settings: Settings | None = None,
                 provider: LLMProvider | None = None):
        self.target = target
        self.settings = settings or get_settings()
        self.provider = provider or get_provider(self.settings)

    def refine(self, script_c: GeneratedScript, *, domain_context: str = "",
               phase=None) -> GeneratedScript:
        from tcgen.progress import NullPhase

        phase = phase or NullPhase()
        t0 = time.time()
        phase.update(0.1, "Refiner: sende Skript_C an LLM (Locator, Oracle, Lesbarkeit)")
        messages: list[Message] = [
            {"role": "system", "content": REFINER_SYSTEM},
            {"role": "user", "content": _user_prompt(
                self.target.base_url, _story_block(self.target.user_stories),
                script_c.code, domain_context)},
        ]
        reply = self.provider.chat(messages)
        code = extract_code_block(reply)
        phase.update(1.0, f"Skript_H erzeugt ({len(code.splitlines())} Zeilen)")
        return GeneratedScript(
            pipeline=Pipeline.HYBRID,
            app_key=self.target.key,
            language="python",
            code=code,
            generation_time_s=round(time.time() - t0, 2),
            model=self.provider.model,
            provider=self.provider.name,
            meta={
                "refined_from": Pipeline.CRAWLER.value,
                "input_element_coverage": script_c.meta.get("element_coverage"),
                "domain_context_used": bool(domain_context.strip()),
            },
        )


def generate(script_c: GeneratedScript, target: TargetApp,
             settings: Settings | None = None, *, domain_context: str = "",
             phase=None) -> GeneratedScript:
    return HybridRefiner(target, settings).refine(
        script_c, domain_context=domain_context, phase=phase)
