"""Completeness denominator: crawler affordances primary, exercised-union fallback."""

from tcgen.orchestration.experiment import ExperimentRunner
from tcgen.orchestration.models import ExecutionResult, Pipeline
from tcgen.runner.metrics import objective


def _ex(locators):
    return ExecutionResult(executed=True, exercised_coverage=len(locators),
                           exercised_locators=list(locators))


def test_exercised_locator_set_and_count():
    code = '''
from playwright.sync_api import Page, expect

def test_a(page: Page):
    page.goto("http://x/")
    page.get_by_role("link", name="Search").first.click()

def test_b(page: Page):
    page.get_by_placeholder("Search").fill("MacBook")
    expect(page.locator("body")).to_be_visible()
'''
    assert objective.exercised_locator_count(code, {"test_a", "test_b"}) == 3
    assert objective.exercised_locator_count(code, {"test_a"}) == 1
    assert objective.exercised_locator_count(code, set()) == 0


def test_denominator_prefers_crawler_affordances():
    # PRIMARY: distinct (role, label) affordances from the crawler catalog —
    # rep-independent — win over the union of exercised locators.
    runner = ExperimentRunner.__new__(ExperimentRunner)  # no heavy __init__ needed

    class _Script:
        meta = {
            "locator_catalog": [
                {"role": "link", "label": "Search", "locator": "l1"},
                {"role": "link", "label": "search", "locator": "l2"},  # same affordance
                {"role": "button", "label": "Add to Basket", "locator": "l3"},
            ],
            "discovered_elements": 99,
        }

    collected = {Pipeline.LLM_AGENT: [(None, _ex({'page.locator("#a")'}), None)]}
    denom, source = runner._coverage_denominator(_Script(), True, collected)
    assert denom == 2  # (link, search) collapsed case-insensitively
    assert source == "crawler_affordances"


def test_denominator_uses_discovered_when_catalog_empty():
    runner = ExperimentRunner.__new__(ExperimentRunner)

    class _Script:
        meta = {"locator_catalog": [], "discovered_elements": 17}

    collected = {Pipeline.LLM_AGENT: [(None, _ex(set()), None)]}
    denom, source = runner._coverage_denominator(_Script(), True, collected)
    assert denom == 17
    assert source == "crawler_discovered"


def test_denominator_falls_back_to_union_without_crawler():
    # FALLBACK: no crawler surface available -> union of exercised locators
    # across pipelines (rep-dependent; flagged via the source string).
    runner = ExperimentRunner.__new__(ExperimentRunner)
    collected = {
        Pipeline.CRAWLER: [(None, _ex({'page.locator("#a")', 'page.locator("#b")'}), None)],
        Pipeline.LLM_AGENT: [(None, _ex({'page.get_by_role("button")', 'page.locator("#a")'}), None)],
    }
    # Union: {#a, #b, button} -> 3 distinct (the shared #a counted once).
    denom, source = runner._coverage_denominator(None, True, collected)
    assert denom == 3
    assert "union" in source


def test_denominator_none_when_no_signal():
    runner = ExperimentRunner.__new__(ExperimentRunner)
    collected = {Pipeline.LLM_AGENT: [(None, _ex(set()), None)]}
    denom, _source = runner._coverage_denominator(None, False, collected)
    assert denom is None
