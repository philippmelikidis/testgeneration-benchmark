"""Execute-verify-repair loop for the LLM pipelines (Skript_L / S / H).

The core problem this fixes: the LLM writes the whole suite BLIND — it never runs
it — so it guesses exact accessible names, pagination, dialog timing, and ~half
its assertions are slightly wrong and the tests go red. This mirrors how a real
developer (or an agentic test tool) actually authors tests: write, RUN, read the
error, fix, run again.

After the initial synthesis, we execute the suite, feed each FAILING test's real
Playwright error back to the model, ask it to fix exactly those functions
(keeping the passing ones), and re-run — keeping whichever version has the higher
SSR (never regressing). Applied IDENTICALLY to every LLM pipeline, so it cannot
bias the comparison; the crawler is deterministic and skips it. Every run records
how many repair rounds were used and the SSR before/after, for full transparency.
"""

from __future__ import annotations

import logging
import time

from config.settings import Settings, TargetApp
from tcgen.llm import LLMProvider, Message
from tcgen.orchestration.models import ExecutionResult, GeneratedScript
from tcgen.progress import NullPhase
from tcgen.util import extract_code_block, postprocess_playwright_code

log = logging.getLogger(__name__)


RUNTIME_REPAIR_SYSTEM = """\
You are a senior test-automation engineer fixing a pytest-playwright suite that
was just RUN against the live application. Some tests FAILED. You are given the
full module and, for each failing test, the REAL Playwright error it produced.

Return the COMPLETE corrected module. Keep every test that already PASSED exactly
as-is; only change the failing ones. Fix them by addressing the actual error:

- "strict mode violation ... resolved to N elements": the locator matches several
  elements. Add `.first` to the LOCATOR (e.g. `page.get_by_role(...).first`), or
  target a more specific, still user-facing locator. Never put `.first` on
  `expect(...)`.
- "Timeout ... waiting for ... to be visible" or "waiting for locator": the
  accessible name / text is slightly wrong, or the element is on another page
  (pagination), or behind an interaction (a menu/dialog must be opened first).
  Use a name/text from the KNOWN APPLICATION SURFACE below, open the required
  menu/dialog first, or — if the item may simply be on another paginated page —
  do NOT assert its visibility; assert the container or the first visible item
  instead (`expect(<list_locator>.first).to_be_visible()`).
- "expected to be visible/attached" on `body` or a route: prefer
  `expect(page.locator("body")).to_be_attached()`.
- Never assert with a bare `.count()` (it does NOT wait); use
  `expect(<locator>.first).to_be_visible()`.

Hard rules (unchanged from generation):
- Do NOT invent selectors, ids, routes, CSS classes, `data-testid`, or component
  tags. Prefer get_by_role / get_by_label / get_by_placeholder / get_by_text with
  real, user-facing names. Ground every reference in the KNOWN APPLICATION SURFACE
  or the elements already used by the passing tests.
- Keep `from playwright.sync_api import Page, expect`; every test takes
  `(page: Page)` and starts with `page.goto(...)`.
- Do NOT weaken tests into no-ops just to make them pass — keep each test
  meaningful for what it verifies.
- Output ONLY the corrected Python module in a single ```python fenced block.
"""


def _repair_prompt(code: str, failures: dict[str, str], base_url: str,
                   app_surface: str = "") -> str:
    fail_block = "\n\n".join(
        f"### FAILING TEST: {fn}\nReal error:\n{msg}"
        for fn, msg in failures.items()
    )
    surface = (f"\nKNOWN APPLICATION SURFACE (real routes/elements discovered by a "
               f"crawler — ground fixes in these):\n{app_surface}\n"
               if app_surface else "")
    return f"""\
BASE URL: {base_url}
{surface}
The following tests FAILED when the suite was executed. Fix exactly these,
keeping the passing tests unchanged:

{fail_block}

Full current module to correct:
```python
{code}
```
"""


def runtime_repair(
    script: GeneratedScript,
    target: TargetApp,
    runner,
    provider: LLMProvider,
    settings: Settings,
    *,
    initial_exec: ExecutionResult | None = None,
    app_surface: str = "",
    max_rounds: int = 2,
    work_tag: str = "",
    phase=None,
) -> tuple[GeneratedScript, ExecutionResult]:
    """Run -> fix-failing-tests -> re-run, keeping the best-SSR version.

    Returns ``(script, execution)`` with ``script.code`` set to the best version
    and repair provenance written into ``script.meta``. ``initial_exec`` lets the
    caller pass an already-computed first run to avoid executing twice.
    """
    phase = phase or NullPhase()
    t0 = time.time()

    if not script.code.strip():
        return script, (initial_exec or ExecutionResult(
            first_error="leeres Skript (LLM lieferte keinen Code)"))

    best_exec = (initial_exec if initial_exec is not None
                 else runner.run(script, phase=phase, work_tag=work_tag))
    best_code = script.code
    ssr_before = round(best_exec.ssr, 4)
    rounds_used = 0

    for r in range(max(0, max_rounds)):
        failures = best_exec.failures or {}
        # Nothing to fix (all green, or the module didn't even run -> a repair on
        # a non-executing module is handled by the static repair round elsewhere).
        if not failures or not best_exec.executed:
            break
        phase.log(f"Laufzeit-Repair Runde {r + 1}/{max_rounds}: "
                  f"{len(failures)} rote Tests → gezielt korrigieren")
        messages: list[Message] = [
            {"role": "system", "content": RUNTIME_REPAIR_SYSTEM},
            {"role": "user", "content": _repair_prompt(
                best_code, failures, target.base_url, app_surface)},
        ]
        try:
            new_code, _fixes = postprocess_playwright_code(
                extract_code_block(provider.chat(messages)))
        except Exception as exc:  # noqa: BLE001
            phase.log(f"Repair-Aufruf fehlgeschlagen ({exc}) — behalte beste Version")
            break
        if not new_code.strip() or new_code == best_code:
            phase.log("Repair brachte keine Änderung — Stop")
            break

        candidate = script.model_copy(update={"code": new_code})
        cand_exec = runner.run(candidate, phase=phase, work_tag=work_tag)
        rounds_used = r + 1
        if cand_exec.ssr > best_exec.ssr:
            phase.log(f"Repair verbesserte SSR {best_exec.ssr:.2f} → {cand_exec.ssr:.2f}")
            best_code, best_exec = new_code, cand_exec
            if best_exec.n_failed == 0:  # all green -> done
                break
        else:
            phase.log(f"Repair ohne SSR-Gewinn ({cand_exec.ssr:.2f} ≤ "
                      f"{best_exec.ssr:.2f}) — behalte vorherige Version, Stop")
            break

    script.code = best_code
    script.meta["runtime_repair_rounds"] = rounds_used
    script.meta["ssr_before_repair"] = ssr_before
    script.meta["ssr_after_repair"] = round(best_exec.ssr, 4)
    script.meta["runtime_repair_time_s"] = round(time.time() - t0, 2)
    return script, best_exec
