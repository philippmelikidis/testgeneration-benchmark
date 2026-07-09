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
    """Static locator count over the whole module (kept for reference only).

    Note: this rewards *hallucinated* locators too — use
    :func:`exercised_locator_count` for the execution-gated metric that feeds
    ISO completeness.
    """
    return len(distinct_locators(code))


def locators_by_function(code: str) -> dict[str, set[str]]:
    """Map each ``test_*`` function name to the distinct locators in its body."""
    defs = [(m.group(1), m.start()) for m in _TESTFN_RE.finditer(code)]
    out: dict[str, set[str]] = {}
    for i, (name, start) in enumerate(defs):
        end = defs[i + 1][1] if i + 1 < len(defs) else len(code)
        body = code[start:end]
        out[name] = {m.group(0).strip() for m in _LOCATOR_RE.finditer(body)}
    return out


def exercised_locator_set(code: str, passed_functions: set[str]) -> set[str]:
    """Distinct locator expressions that appear in test functions that PASSED.

    The execution-gated coverage *set* (the count proxy builds on this): locators
    in failing tests (including hallucinated ones, which cause the failure) are
    excluded, so it reflects elements the suite genuinely exercised. Returning the
    set — not just its size — lets the orchestrator union exercised locators
    across pipelines to form a pipeline-neutral completeness denominator.
    """
    by_fn = locators_by_function(code)
    used: set[str] = set()
    for fn in passed_functions:
        used |= by_fn.get(fn, set())
    return used


def exercised_locator_count(code: str, passed_functions: set[str]) -> int:
    """Number of distinct locators exercised by passing tests (see
    :func:`exercised_locator_set`)."""
    return len(exercised_locator_set(code, passed_functions))


def assertion_count(code: str) -> int:
    return len(_ASSERT_RE.findall(code))


def test_function_names(code: str) -> list[str]:
    return _TESTFN_RE.findall(code)


def _passing_bodies(code: str, passed_functions: set[str]) -> list[str]:
    """Return the source bodies of the test functions that passed (lower-cased)."""
    defs = [(m.group(1), m.start()) for m in _TESTFN_RE.finditer(code)]
    bodies: list[str] = []
    for i, (name, start) in enumerate(defs):
        if name not in passed_functions:
            continue
        end = defs[i + 1][1] if i + 1 < len(defs) else len(code)
        bodies.append(code[start:end].lower())
    return bodies


def story_coverage(code: str, passed_functions: set[str],
                   story_key_elements: list[list[str]]) -> tuple[int, int]:
    """Requirement-based functional completeness.

    Returns ``(covered, total)`` where a user story counts as *covered* iff some
    PASSING test references ALL of the story's signature elements (case-insensitive
    substrings — the real accessible names the app exposes). This measures the
    ISO/IEC 25010 sense of completeness — "share of the specified user objectives
    covered" — instead of "share of every element in the whole app", and is
    applied identically to every pipeline. Stories with no declared signatures are
    excluded from the total (they cannot be measured objectively).
    """
    measurable = [ke for ke in story_key_elements if ke]
    if not measurable:
        return 0, 0
    bodies = _passing_bodies(code, passed_functions)
    covered = 0
    for keys in measurable:
        needles = [k.lower() for k in keys]
        if any(all(n in body for n in needles) for body in bodies):
            covered += 1
    return covered, len(measurable)


def successful_steps_ratio(n_passed: int, n_tests: int) -> float:
    """SSR at test-case granularity: passed / total (0.0 if no tests)."""
    return round(n_passed / n_tests, 4) if n_tests else 0.0
