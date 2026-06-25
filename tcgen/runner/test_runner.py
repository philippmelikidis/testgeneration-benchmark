"""Execute a generated script via pytest-playwright and collect objective metrics."""

from __future__ import annotations

import json
import logging
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

import re
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
    ):
        try:
            locators.append(_factory())
        except Exception:
            pass
    for _loc in locators:
        try:
            # no_wait_after=True: don't wait for the overlay to visually disappear
            # after clicking. Without it Playwright re-fires the handler until the
            # element is hidden, which creates a 10+ iteration loop on animated
            # banners (e.g. Juice Shop cookie bar) and leaves page.url as None,
            # breaking subsequent expect(page) assertions.
            page.add_locator_handler(
                _loc,
                lambda *a, loc=_loc: loc.first.click(timeout=2000),
                no_wait_after=True,
            )
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _harness(page):
    page.set_default_timeout({timeout})
    _register_overlay_handlers(page)
    yield
'''


class TestRunner:
    def __init__(self, settings: Settings | None = None, *, run_timeout_s: int = 300):
        self.settings = settings or get_settings()
        self.run_timeout_s = run_timeout_s

    def run(self, script: GeneratedScript, phase=None) -> ExecutionResult:
        from tcgen.progress import NullPhase

        phase = phase or NullPhase()
        path = self._materialise(script)
        runs: list[dict] = []
        n = max(1, self.settings.flakiness_runs)
        for i in range(n):
            phase.update(i / n, f"pytest-Lauf {i + 1}/{n} ({script.pipeline.script_label})")
            runs.append(self._run_once(path, label=f"{script.pipeline.value}_{i}"))
        phase.update(1.0, f"Ausführung fertig: {runs[0]['n_passed']}/{runs[0]['n_tests']} grün")

        first = runs[0]
        n_tests = first["n_tests"]
        n_passed = first["n_passed"]
        n_failed = first["n_failed"]

        # Which test functions passed -> execution-gated ("exercised") coverage.
        passed_fns = {
            nodeid.split("::")[-1]
            for nodeid, outcome in first.get("outcomes", {}).items()
            if outcome == "passed"
        }

        return ExecutionResult(
            executed=first["executed"],
            passed=(n_tests > 0 and n_failed == 0 and first["executed"]),
            n_tests=n_tests,
            n_passed=n_passed,
            n_failed=n_failed,
            duration_s=round(first["duration"], 2),
            ssr=objective.successful_steps_ratio(n_passed, n_tests),
            element_coverage=objective.element_coverage(script.code),
            exercised_coverage=objective.exercised_locator_count(script.code, passed_fns),
            flakiness=self._flakiness(runs),
            first_error=first.get("first_error"),
            stdout=first["stdout"][-4000:],
            stderr=first["stderr"][-4000:],
        )

    # ------------------------------------------------------------------ #
    def _materialise(self, script: GeneratedScript) -> Path:
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
            selectors = load_target(app_key).dismiss_selectors
        except Exception:  # noqa: BLE001
            selectors = []
        conftest = _CONFTEST_TEMPLATE.format(
            timeout=self.settings.test_action_timeout_ms,
            selectors=repr(list(selectors)),
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
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.run_timeout_s,
                cwd=str(GENERATED_DIR.parent),
            )
            stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            return {"executed": False, "n_tests": 0, "n_passed": 0, "n_failed": 0,
                    "duration": float(self.run_timeout_s), "outcomes": {},
                    "first_error": "TIMEOUT: Gesamtlauf überschritt run_timeout_s",
                    "stdout": exc.stdout or "", "stderr": "TIMEOUT"}

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
                "duration": 0.0, "outcomes": {}, "first_error": None}
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
