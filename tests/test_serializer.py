from config.settings import TargetApp
from tcgen.pipelines.crawler.crawler import CrawlOutput
from tcgen.pipelines.crawler.serializer import _element_coverage, serialize
from tcgen.pipelines.crawler.state import Action, ElementDescriptor


def _target():
    return TargetApp(key="demoshop", name="Demo Shop",
                     base_url="http://localhost:8080")


def _crawl():
    link = ElementDescriptor(tag="a", text="Search", href="/search")
    scenario = [
        Action(kind="goto", url="http://localhost:8080/"),
        Action(kind="click", element=link),
    ]
    return CrawlOutput(app_key="demoshop", scenarios=[scenario],
                       n_states=3, n_edges=2, elapsed_s=1.0)


def test_serialize_produces_valid_pytest_module():
    code = serialize(_crawl(), _target())
    assert "import pytest" in code
    assert "from playwright.sync_api import Page, expect" in code
    assert "def test_scenario_1(page: Page)" in code
    assert 'page.goto("http://localhost:8080/")' in code
    assert 'expect(page.locator("body")).to_be_attached()' in code


def test_serialized_module_compiles():
    code = serialize(_crawl(), _target())
    compile(code, "<skript_c>", "exec")  # must be syntactically valid Python


def test_element_coverage_counts_distinct_elements():
    assert _element_coverage(_crawl()) == 1
