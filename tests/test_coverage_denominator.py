"""Completeness denominator: pipeline-neutral union of exercised locators."""

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


def test_denominator_unions_across_pipelines():
    runner = ExperimentRunner.__new__(ExperimentRunner)  # no heavy __init__ needed
    collected = {
        Pipeline.CRAWLER: [(None, _ex({'page.locator("#a")', 'page.locator("#b")'}), None)],
        Pipeline.LLM_AGENT: [(None, _ex({'page.get_by_role("button")', 'page.locator("#a")'}), None)],
    }
    # Union: {#a, #b, button} -> 3 distinct (the shared #a counted once).
    assert runner._coverage_denominator(None, True, collected) == 3


def test_denominator_falls_back_to_crawler_when_nothing_exercised():
    runner = ExperimentRunner.__new__(ExperimentRunner)

    class _Script:
        meta = {"discovered_elements": 17}

    collected = {Pipeline.LLM_AGENT: [(None, _ex(set()), None)]}
    assert runner._coverage_denominator(_Script(), True, collected) == 17


def test_denominator_none_when_no_signal():
    runner = ExperimentRunner.__new__(ExperimentRunner)
    collected = {Pipeline.LLM_AGENT: [(None, _ex(set()), None)]}
    assert runner._coverage_denominator(None, False, collected) is None
