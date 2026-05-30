from tcgen.orchestration.models import ExecutionResult, JudgeScores
from tcgen.runner.metrics import objective
from tcgen.runner.metrics.iso25010 import COVERAGE_REFERENCE, map_to_iso

SAMPLE = '''
from playwright.sync_api import Page, expect

def test_a(page: Page):
    page.goto("http://x/")
    page.get_by_role("link", name="Search").first.click()
    expect(page).not_to_have_url("about:blank")

def test_b(page: Page):
    page.get_by_placeholder("Search").fill("MacBook")
    expect(page.locator("body")).to_be_visible()
'''


def test_distinct_locators_and_coverage():
    locs = objective.distinct_locators(SAMPLE)
    # three distinct locator expressions
    assert objective.element_coverage(SAMPLE) == len(locs) == 3


def test_assertion_and_testfn_counts():
    assert objective.assertion_count(SAMPLE) == 2
    assert objective.test_function_names(SAMPLE) == ["test_a", "test_b"]


def test_ssr():
    assert objective.successful_steps_ratio(2, 2) == 1.0
    assert objective.successful_steps_ratio(1, 2) == 0.5
    assert objective.successful_steps_ratio(0, 0) == 0.0


def test_iso_mapping_combines_objective_and_judge():
    ex = ExecutionResult(executed=True, ssr=1.0, element_coverage=10)
    jd = JudgeScores(correctness=0.8, appropriateness=0.6, hallucination=0.2)
    iso = map_to_iso(ex, jd)
    assert iso.functional_correctness == 0.9          # mean(0.8, 1.0)
    norm_cov = min(10 / COVERAGE_REFERENCE, 1.0)       # 0.5
    assert iso.functional_completeness == round((norm_cov + 1.0) / 2, 4)
    assert iso.functional_appropriateness == 0.7       # mean(0.6, 1-0.2)
    assert iso.overall is not None


def test_iso_mapping_handles_missing_judge():
    ex = ExecutionResult(executed=False, ssr=0.0, element_coverage=0)
    iso = map_to_iso(ex, JudgeScores())
    # correctness falls back to ssr(=0 because not executed)
    assert iso.functional_correctness == 0.0
    assert iso.functional_appropriateness is None
