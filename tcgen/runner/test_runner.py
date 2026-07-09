"""Execute a generated script via pytest-playwright and collect objective metrics."""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from config.settings import GENERATED_DIR, Settings, get_settings, load_target
from tcgen.orchestration.models import ExecutionResult, GeneratedScript
from tcgen.runner.metrics import objective

log = logging.getLogger(__name__)

# Shared pytest harness written next to every generated script. Applied
# uniformly to all pipelines so the comparison stays fair: it (a) bounds the
# per-action timeout so broken scripts fail fast instead of hanging on the 30s
# Playwright default, and (b) auto-dismisses welcome dialogs / cookie banners
# after each navigation (these otherwise intercept every click on SPAs).
_CONFTEST_TEMPLATE = '''\
"""Auto-generated shared test harness (do not edit; rewritten on each run)."""

import pytest


_DISMISS_SELECTORS = {selectors}


def _register_overlay_handlers(page):
    """Auto-dismiss welcome/cookie overlays whenever they would block an action.

    Uses Playwright's add_locator_handler: the engine itself invokes the handler
    when one of these overlays intercepts an action, then retries it. Robust (no
    monkeypatching) and applied identically to every pipeline.

    Target-specific CSS selectors (from the target config) come first because
    they are the most reliable; generic role-based locators are fallbacks. Regex
    names are deliberately avoided — they raise InvalidSelectorError in
    Playwright's selector engine.
    """
    locators = []
    for _sel in _DISMISS_SELECTORS:
        try:
            locators.append(page.locator(_sel))
        except Exception:
            pass
    for _factory in (
        lambda: page.get_by_role("button", name="dismiss cookie message"),
        lambda: page.get_by_role("button", name="Close Welcome Banner"),
        lambda: page.locator(".close-dialog"),  # welcome dialog close (single match)
    ):
        try:
            locators.append(_factory())
        except Exception:
            pass

    def _make_handler(loc):
        def _handler(*_a):
            try:
                loc.first.click(timeout=1500)
            except Exception:
                pass  # handler must never raise, or it fails the test
        return _handler

    for _loc in locators:
        try:
            # no_wait_after=True: dismiss and continue immediately. Without it,
            # Playwright loops waiting for the overlay to disappear (which it may
            # not, if another modal sits on top), corrupting the action.
            # times=1: dismiss once per test; banner won't reappear mid-test.
            page.add_locator_handler(
                _loc, _make_handler(_loc),
                no_wait_after=True,
                times=1,
            )
        except TypeError:
            page.add_locator_handler(_loc, _make_handler(_loc))  # older Playwright
        except Exception:
            pass

    # NOTE: the transparent CDK backdrop (mat-menu / mat-select) is handled by
    # _KILL_TRANSPARENT_BACKDROP_JS (an init script that removes the node), NOT by
    # a reactive Escape handler. Escape was WRONG: add_locator_handler fires the
    # handler whenever the backdrop is merely VISIBLE — which it always is while a
    # menu/dropdown/search overlay is open — so it pressed Escape and closed the
    # very menu/search field the test was navigating (login/register items vanish;
    # the search input detaches mid-fill -> "element was detached from the DOM").
    # Removing only the backdrop node leaves the overlay pane (menu items, select
    # options, search field) open and clickable, and nothing intercepts the click.

# Disable CSS animations/transitions so Material ripples and route transitions
# don't leave elements "unstable" (Playwright then retries a click until timeout
# and the test fails spuriously). Injected on every document via an init script,
# so it applies after each navigation. Part of the shared evaluation harness ->
# applied identically to every pipeline, so it cannot bias the comparison.
_NO_ANIM_JS = """
(() => {{
  const css = '*,*::before,*::after{{animation-duration:0s!important;' +
    'animation-delay:0s!important;transition-duration:0s!important;' +
    'transition-delay:0s!important;scroll-behavior:auto!important;}}';
  const apply = () => {{
    const s = document.createElement('style');
    s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  }};
  if (document.head) apply();
  else document.addEventListener('DOMContentLoaded', apply);
}})();
"""


# Pre-seed the "already dismissed" state so first-visit overlays (welcome
# dialog, cookie banner) never appear. This is the reliable fix for the failure
# where a welcome MODAL marks the rest of the app aria-hidden, so role-based
# locators can't find anything and time out — reactive overlay handlers fire
# too late for that. The keys come from the target config
# (``predismiss_storage``), NOT from app-specific hard-coding in this shared
# harness; applied identically to every pipeline (not result tuning).
_PREDISMISS_JS = {predismiss_js}


# Juice Shop leaves the DISMISSED cookie-consent banner in the DOM as a hidden
# `<div role="dialog" aria-label="cookieconsent" class="cc-window cc-invisible">`.
# That ghost node collides with EVERY dialog query — `get_by_role("dialog")` and
# `page.locator("[role=dialog]").first` resolve to it (hidden) instead of the real
# product/detail dialog, so the assertion times out on "hidden". The banner is
# already dismissed (see _PREDISMISS_JS); removing its leftover node is cleanup of
# an already-dismissed overlay, applied identically to every pipeline — it removes
# spurious noise, it does not favour any generation strategy.
_KILL_COOKIECONSENT_JS = """
(() => {{
  const kill = () => document.querySelectorAll(
    '.cc-window, [aria-label="cookieconsent"]').forEach((n) => n.remove());
  const start = () => {{
    kill();
    try {{
      new MutationObserver(kill).observe(
        document.documentElement, {{childList: true, subtree: true}});
    }} catch (e) {{}}
  }};
  if (document.documentElement) start();
  else document.addEventListener('DOMContentLoaded', start);
}})();
"""


# Angular Material menus/dropdowns/selects (account menu, "Items per page",
# "Security Question", the expanded search field) render a *transparent* CDK
# backdrop whose ONLY job is to catch an outside-click to close the panel. While
# open it sits over the whole page and intercepts the next click/fill, so tests
# time out with "<...> intercepts pointer events". Removing just the backdrop
# NODE (not the overlay pane) leaves the menu items / select options / search
# field fully open and clickable while nothing can intercept — verified live that
# it neither breaks the account menu -> login flow nor the (dark-backdrop)
# product dialog. Scoped to `.cdk-overlay-transparent-backdrop` ON PURPOSE: modal
# dialogs use `.cdk-overlay-dark-backdrop` and are left untouched. Harness-level,
# applied identically to every pipeline (mirrors the cookie-ghost cleanup above).
_KILL_TRANSPARENT_BACKDROP_JS = """
(() => {{
  const kill = () => document.querySelectorAll(
    '.cdk-overlay-transparent-backdrop').forEach((n) => n.remove());
  const start = () => {{
    kill();
    try {{
      new MutationObserver(kill).observe(
        document.documentElement, {{childList: true, subtree: true}});
    }} catch (e) {{}}
  }};
  if (document.documentElement) start();
  else document.addEventListener('DOMContentLoaded', start);
}})();
"""


@pytest.fixture(autouse=True)
def _harness(page):
    page.set_default_timeout({timeout})
    for _script in (_PREDISMISS_JS, _KILL_COOKIECONSENT_JS,
                    _KILL_TRANSPARENT_BACKDROP_JS, _NO_ANIM_JS):
        if not _script:
            continue
        try:
            page.add_init_script(_script)
        except Exception:
            pass
    _register_overlay_handlers(page)  # fallback for anything still shown
    yield
'''


def _predismiss_js(storage: dict[str, str]) -> str:
    """Build the pre-seed init script from the target's predismiss config."""
    if not storage:
        return ""
    stmts = []
    for key, value in storage.items():
        stmts.append(f"try {{ localStorage.setItem({json.dumps(key)},"
                     f"{json.dumps(value)}); }} catch(e) {{}}")
        stmts.append(f"try {{ document.cookie = {json.dumps(f'{key}={value}; path=/')}; }}"
                     f" catch(e) {{}}")
    return "(() => { " + " ".join(stmts) + " })();"


class TestRunner:
    def __init__(self, settings: Settings | None = None, *, run_timeout_s: int = 300):
        self.settings = settings or get_settings()
        self.run_timeout_s = run_timeout_s

    def run(self, script: GeneratedScript, phase=None,
            work_tag: str = "") -> ExecutionResult:
        from tcgen.progress import NullPhase

        phase = phase or NullPhase()
        # ``work_tag`` isolates a run's scratch files (test module + conftest +
        # json report) into their own directory, so several repetitions of the
        # SAME pipeline can execute CONCURRENTLY without overwriting each other's
        # ``test_<pipeline>.py``. Empty -> the shared canonical path (sequential).
        path = self._materialise(script, work_tag)
        runs: list[dict] = []
        n = max(1, self.settings.flakiness_runs)
        label_base = f"{work_tag}_{script.pipeline.value}" if work_tag else script.pipeline.value
        for i in range(n):
            phase.update(i / n, f"pytest-Lauf {i + 1}/{n} ({script.pipeline.script_label})")
            runs.append(self._run_once(path, label=f"{label_base}_{i}"))
        phase.update(1.0, f"Ausführung fertig: {runs[0]['n_passed']}/{runs[0]['n_tests']} grün")

        first = runs[0]
        n_tests = first["n_tests"]
        n_passed = first["n_passed"]
        n_failed = first["n_failed"]

        # Which test functions passed -> execution-gated ("exercised") coverage.
        # Strip the pytest-playwright parametrisation suffix, e.g.
        # "test_x[chromium]" -> "test_x", so it matches the function names in the
        # source (otherwise exercised coverage is always 0).
        passed_fns = {
            nodeid.split("::")[-1].split("[")[0]
            for nodeid, outcome in first.get("outcomes", {}).items()
            if outcome == "passed"
        }
        exercised = objective.exercised_locator_set(script.code, passed_fns)

        return ExecutionResult(
            executed=first["executed"],
            passed=(n_tests > 0 and n_failed == 0 and first["executed"]),
            n_tests=n_tests,
            n_passed=n_passed,
            n_failed=n_failed,
            duration_s=round(first["duration"], 2),
            ssr=objective.successful_steps_ratio(n_passed, n_tests),
            element_coverage=objective.element_coverage(script.code),
            exercised_coverage=len(exercised),
            exercised_locators=sorted(exercised),
            flakiness=self._flakiness(runs),
            first_error=first.get("first_error"),
            failures=first.get("failures", {}),
            passed_functions=sorted(passed_fns),
            stdout=first["stdout"][-4000:],
            stderr=first["stderr"][-4000:],
        )

    # ------------------------------------------------------------------ #
    def _materialise(self, script: GeneratedScript, work_tag: str = "") -> Path:
        # Concurrent reps get an isolated scratch dir; the canonical (unsuffixed)
        # location is kept for sequential runs so the on-disk artefact stays where
        # tooling expects it. The UI reads code from the record, not these files.
        # Isolated dirs are SIBLINGS of the app dir (generated/.work/<app>_<tag>),
        # NOT children of generated/<app>/ — otherwise pytest would also load that
        # dir's leftover conftest.py and double-apply the autouse harness fixture.
        if work_tag:
            out_dir = GENERATED_DIR / ".work" / f"{script.app_key}_{work_tag}"
        else:
            out_dir = GENERATED_DIR / script.app_key
        out_dir.mkdir(parents=True, exist_ok=True)
        self._write_conftest(out_dir, script.app_key)
        path = out_dir / f"test_{script.pipeline.value}.py"
        path.write_text(script.code, encoding="utf-8")
        if script.path is None:
            script.path = str(path)
        return path

    def _write_conftest(self, out_dir: Path, app_key: str) -> None:
        try:
            target = load_target(app_key)
            selectors = target.dismiss_selectors
            predismiss = getattr(target, "predismiss_storage", {}) or {}
        except Exception:  # noqa: BLE001
            selectors, predismiss = [], {}
        conftest = _CONFTEST_TEMPLATE.format(
            timeout=self.settings.test_action_timeout_ms,
            selectors=repr(list(selectors)),
            predismiss_js=repr(_predismiss_js(predismiss)),
        )
        (out_dir / "conftest.py").write_text(conftest, encoding="utf-8")

    def _run_once(self, path: Path, *, label: str) -> dict:
        report = Path(tempfile.gettempdir()) / f"tcgen_report_{label}.json"
        cmd = [
            sys.executable, "-m", "pytest", str(path),
            "-p", "no:cacheprovider", "-q",
            "--browser", "chromium",
            "--json-report", f"--json-report-file={report}",
        ]
        if not self.settings.headless:
            cmd.append("--headed")
        # Run in its own process group so a timeout can kill the WHOLE tree
        # (pytest + the chromium it spawned). With plain subprocess.run(timeout=)
        # only the direct child is killed; the browser keeps the stdout pipe open
        # and the call blocks far beyond the timeout (the "20-minute run").
        #
        # stdin=DEVNULL is CRITICAL: the Streamlit background worker runs detached,
        # so its own stdin (fd 0) is closed/invalid. Without this, the pytest child
        # INHERITS that broken fd 0 and Python aborts at startup with
        # "Fatal Python error: init_sys_streams: can't initialize sys standard
        # streams / OSError: [Errno 9] Bad file descriptor" — intermittently, which
        # silently tanks SSR over many runs. Giving the child a real /dev/null stdin
        # fixes it deterministically.
        proc = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=str(GENERATED_DIR.parent), start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=self.run_timeout_s)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
            try:
                stdout, stderr = proc.communicate(timeout=15)
            except Exception:  # noqa: BLE001
                stdout, stderr = "", "TIMEOUT"
            return {"executed": False, "n_tests": 0, "n_passed": 0, "n_failed": 0,
                    "duration": float(self.run_timeout_s), "outcomes": {},
                    "first_error": (f"TIMEOUT: Gesamtlauf überschritt "
                                    f"{self.run_timeout_s}s (hart abgebrochen)"),
                    "stdout": stdout or "", "stderr": stderr or "TIMEOUT"}

        parsed = self._parse_report(report)
        # "executed" means: the module imported/collected AND ran at least one
        # test. rc 2 = usage/collection error, rc 5 = no tests collected; both
        # mean the script is not a usable test suite.
        parsed["executed"] = (
            rc not in (2, 5)
            and parsed["n_tests"] > 0
            and "INTERNALERROR" not in stderr
        )
        parsed["stdout"] = stdout
        parsed["stderr"] = stderr
        return parsed

    @staticmethod
    def _parse_report(report: Path) -> dict:
        base = {"executed": False, "n_tests": 0, "n_passed": 0, "n_failed": 0,
                "duration": 0.0, "outcomes": {}, "first_error": None, "failures": {}}
        if not report.exists():
            return base
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return base
        summary = data.get("summary", {})
        tests = data.get("tests", [])
        outcomes = {t.get("nodeid", str(i)): t.get("outcome", "error")
                    for i, t in enumerate(tests)}
        return {
            "n_tests": summary.get("total", len(tests)),
            "n_passed": summary.get("passed", 0),
            "n_failed": summary.get("failed", 0) + summary.get("error", 0),
            "duration": data.get("duration", 0.0),
            "outcomes": outcomes,
            "first_error": _first_failure_message(tests),
            "failures": _per_test_failures(tests),
        }

    @staticmethod
    def _flakiness(runs: list[dict]) -> float:
        """Fraction of tests whose pass/fail outcome was not unanimous across runs."""
        if len(runs) < 2:
            return 0.0
        per_test: dict[str, set[str]] = defaultdict(set)
        for r in runs:
            for nodeid, outcome in r.get("outcomes", {}).items():
                per_test[nodeid].add("passed" if outcome == "passed" else "failed")
        if not per_test:
            return 0.0
        unstable = sum(1 for outcomes in per_test.values() if len(outcomes) > 1)
        return round(unstable / len(per_test), 4)


def _first_failure_message(tests: list[dict]) -> str | None:
    """Return a short message for the first failing/erroring test in the report."""
    for t in tests:
        if t.get("outcome") not in ("failed", "error"):
            continue
        for phase in ("call", "setup", "teardown"):
            info = t.get(phase) or {}
            crash = info.get("crash") or {}
            msg = crash.get("message") or info.get("longrepr")
            if msg:
                node = t.get("nodeid", "").split("::")[-1]
                return f"{node}: {str(msg).strip().splitlines()[-1][:400]}"
    return None


def _per_test_failures(tests: list[dict]) -> dict[str, str]:
    """Map each failing test FUNCTION -> a short real error message.

    Feeds the execute-verify-repair loop: the LLM is asked to fix exactly these
    functions against their actual Playwright error, instead of guessing blind.
    The message is the last few lines of the crash/longrepr (where the concrete
    Playwright error — 'strict mode violation', 'Timeout ... waiting for locator',
    'expected to be visible' — lives), trimmed to keep the repair prompt compact.
    """
    out: dict[str, str] = {}
    for t in tests:
        if t.get("outcome") not in ("failed", "error"):
            continue
        fn = t.get("nodeid", "").split("::")[-1].split("[")[0]
        if not fn or fn in out:
            continue
        msg = None
        for phase in ("call", "setup", "teardown"):
            info = t.get(phase) or {}
            crash = info.get("crash") or {}
            msg = crash.get("message") or info.get("longrepr")
            if msg:
                break
        if msg:
            lines = [ln for ln in str(msg).strip().splitlines() if ln.strip()]
            out[fn] = "\n".join(lines[-6:])[:600]
    return out
