"""LLM refiner: Skript_C -> Skript_H (Methode 2)."""

from __future__ import annotations

import time

from config.settings import Settings, TargetApp, get_settings
from tcgen.llm import LLMProvider, Message, get_provider
from tcgen.orchestration.models import GeneratedScript, Pipeline
from tcgen.pipelines.llm_agent.agent import _story_block
from tcgen.util import extract_code_block, postprocess_playwright_code

REFINER_SYSTEM = """\
You are a senior test automation engineer. You are given the output of an
autonomous crawler that already explored the target application: its discovered
ROUTES and a CATALOG of the REAL, verified locators it actually used (each with
the element's visible label and ARIA role), plus a working example test module
(Skript_C) built from those locators. Using this crawler map as your ground
truth, WRITE a pytest-playwright test suite that VERIFIES the given user stories.

This is grounded generation, not a cosmetic refactor:
- Treat the ROUTES and the LOCATOR CATALOG as the only elements that exist in the
  app. Build each test from them: navigate to the relevant route, drive the flow
  with catalog locators, and assert the story's acceptance criteria.
- Prefer the catalog's user-facing locators (get_by_role/label/placeholder/text
  with the labels shown). You MAY reuse the exact locator expressions from
  Skript_C / the catalog verbatim — they are known to work.
- Write one test function per user story (named after it), plus optional extra
  flows that the catalog clearly supports.

GROUNDING — hard rules (you have NOT seen the live DOM; the crawler map is your
only source of truth):
- NEVER invent selectors that are absent from the catalog/Skript_C: no made-up
  CSS classes (e.g. `.product-card`, `.price`), ids, component tags (`app-*`),
  placeholders, ARIA roles, or routes.
- If a story's acceptance criterion cannot be grounded in the catalog, assert it
  conservatively (e.g. the relevant route is reachable, `expect(page.locator(
  "body")).to_be_attached()`) rather than inventing app-specific selectors.
- Do not use exact `to_have_url(...)` equality (SPA hash routes vary); use a
  substring/regex check if you assert the URL at all.
- A locator may match MULTIPLE elements (e.g. `mat-card`, product cards). Never
  call `.click()`/`expect(...).to_be_visible()` on a multi-match locator (it
  raises a strict-mode error). Use `.first` (e.g. `loc.first`) or assert the
  count. For "at least one", use `assert loc.count() > 0` — do NOT invent
  Playwright methods. ONLY these expect assertions exist: `to_be_visible`,
  `to_be_attached`, `to_have_count(n)`, `to_have_text(...)`, `to_contain_text(...)`,
  `to_have_url(...)`. There is NO `to_have_count_greater_than`.

Constraints:
- A runnable pytest-playwright module using the `page: Page` fixture; import
  exactly `from playwright.sync_api import Page, expect`.
- Every test starts with `page.goto("<BASE_URL>...")`.
- A shared harness already dismisses welcome/cookie overlays and bounds timeouts.
- Output ONLY the Python code in a single ```python fenced block.
"""


def _format_catalog(catalog: list[dict], limit: int = 120) -> str:
    if not catalog:
        return "(no catalog available — fall back to the locators in Skript_C below)"
    lines = []
    for c in catalog[:limit]:
        label = (c.get("label") or "").strip()
        role = c.get("role") or ""
        loc = c.get("locator") or ""
        url = (c.get("url") or "").strip()
        where = f"  [route: {url}]" if url else ""
        lines.append(f'- {role} "{label}"  ->  {loc}{where}')
    return "\n".join(lines)


def _user_prompt(base_url: str, story_block: str, script_c: str,
                 domain_context: str = "", catalog: list[dict] | None = None,
                 routes: list[str] | None = None) -> str:
    domain = domain_context.strip()
    domain_section = (
        f"\nDOMAIN / EXPERT CONTEXT (use to make assertions more meaningful):\n{domain}\n"
        if domain else ""
    )
    routes_section = ""
    if routes:
        routes_section = "\nDISCOVERED ROUTES (real, reachable):\n" + \
            "\n".join(f"- {r}" for r in routes[:40]) + "\n"
    return f"""\
BASE URL: {base_url}

USER STORIES TO VERIFY (one test each):
{story_block}
{domain_section}{routes_section}
CRAWLER LOCATOR CATALOG (real, verified elements — role "label" -> Playwright locator):
{_format_catalog(catalog or [])}

WORKING EXAMPLE (Skript_C — these locators are known to run against the app):
```python
{script_c}
```

Now write the grounded pytest-playwright suite (Skript_H) that verifies the user
stories using ONLY the routes/locators above. Descriptive, story-referencing names.
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
        catalog = script_c.meta.get("locator_catalog") or []
        routes = script_c.meta.get("routes") or []
        phase.update(0.1, f"Refiner: grounded Generierung aus Crawler-Map "
                          f"({len(catalog)} Locator, {len(routes)} Routen) + Stories")
        messages: list[Message] = [
            {"role": "system", "content": REFINER_SYSTEM},
            {"role": "user", "content": _user_prompt(
                self.target.base_url, _story_block(self.target.user_stories),
                script_c.code, domain_context, catalog=catalog, routes=routes)},
        ]
        reply = self.provider.chat(messages)
        code = postprocess_playwright_code(extract_code_block(reply))
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
                "grounded_locators": len(catalog),
                "grounded_routes": len(routes),
            },
        )


def generate(script_c: GeneratedScript, target: TargetApp,
             settings: Settings | None = None, *, domain_context: str = "",
             phase=None) -> GeneratedScript:
    return HybridRefiner(target, settings).refine(
        script_c, domain_context=domain_context, phase=phase)
