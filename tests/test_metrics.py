from tcgen.orchestration.models import ExecutionResult, JudgeScores
from tcgen.runner.metrics import objective
from tcgen.runner.metrics.iso25010 import map_to_iso

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


def test_static_element_coverage_counts_all_locators():
    assert objective.element_coverage(SAMPLE) == 3


def test_locators_by_function_splits_per_test():
    by_fn = objective.locators_by_function(SAMPLE)
    assert set(by_fn) == {"test_a", "test_b"}
    assert len(by_fn["test_a"]) == 1
    assert len(by_fn["test_b"]) == 2


def test_exercised_coverage_only_counts_passing_tests():
    assert objective.exercised_locator_count(SAMPLE, {"test_a", "test_b"}) == 3
    assert objective.exercised_locator_count(SAMPLE, {"test_a"}) == 1
    assert objective.exercised_locator_count(SAMPLE, set()) == 0  # nothing passed


def test_ssr():
    assert objective.successful_steps_ratio(2, 2) == 1.0
    assert objective.successful_steps_ratio(1, 2) == 0.5
    assert objective.successful_steps_ratio(0, 0) == 0.0


def test_iso_uses_continuous_passrate_and_real_denominator():
    ex = ExecutionResult(executed=True, ssr=0.9, exercised_coverage=10)
    jd = JudgeScores(correctness=0.8, appropriateness=0.6, hallucination=0.2)
    iso = map_to_iso(ex, jd, coverage_denominator=20)
    assert iso.functional_correctness == 0.85          # mean(0.8, 0.9) — continuous
    assert iso.functional_completeness == 0.5           # 10 / 20 (real denominator)
    assert iso.functional_appropriateness == 0.6        # = judge appropriateness (consistent)


def test_iso_completeness_zero_when_nothing_exercised():
    ex = ExecutionResult(executed=True, ssr=0.0, exercised_coverage=0)
    iso = map_to_iso(ex, JudgeScores(correctness=0.5), coverage_denominator=20)
    assert iso.functional_completeness == 0.0


def test_iso_completeness_none_without_denominator():
    ex = ExecutionResult(executed=True, ssr=1.0, exercised_coverage=5)
    iso = map_to_iso(ex, JudgeScores(), coverage_denominator=None)
    assert iso.functional_completeness is None
