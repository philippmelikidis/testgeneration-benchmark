"""Static, deterministic metrics derived from the script source.

These need no LLM and no running app, so they are unit-testable in isolation.
"""

from __future__ import annotations

import re

# Playwright locator-producing calls. Counting *distinct* calls gives a
# cross-pipeline-comparable proxy for "element coverage".
_LOCATOR_RE = re.compile(
    r"""
    (?:page|frame)\.
    (?:get_by_role|get_by_text|get_by_label|get_by_placeholder|
       get_by_test_id|get_by_title|get_by_alt_text|locator)
    \([^\n]*?\)
    """,
    re.VERBOSE,
)
_ASSERT_RE = re.compile(r"\bexpect\s*\(")
_TESTFN_RE = re.compile(r"^def\s+(test_\w+)\s*\(", re.MULTILINE)


def distinct_locators(code: str) -> set[str]:
    """Return the set of distinct locator expressions used in the script."""
    return {m.group(0).strip() for m in _LOCATOR_RE.finditer(code)}


def element_coverage(code: str) -> int:
    return len(distinct_locators(code))


def assertion_count(code: str) -> int:
    return len(_ASSERT_RE.findall(code))


def test_function_names(code: str) -> list[str]:
    return _TESTFN_RE.findall(code)


def successful_steps_ratio(n_passed: int, n_tests: int) -> float:
    """SSR at test-case granularity: passed / total (0.0 if no tests)."""
    return round(n_passed / n_tests, 4) if n_tests else 0.0
