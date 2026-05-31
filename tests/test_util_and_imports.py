import importlib

from tcgen.util import (
    extract_code_block,
    extract_json_object,
    model_family,
    same_model_family,
    validate_playwright_code,
)


def test_validate_playwright_code_accepts_clean_module():
    good = (
        "from playwright.sync_api import Page, expect\n\n"
        "def test_a(page: Page):\n"
        '    page.goto("http://x/")\n'
        '    page.get_by_role("link", name="A").click()\n'
        '    expect(page.locator("body")).to_be_visible()\n'
    )
    assert validate_playwright_code(good) == []


def test_validate_playwright_code_flags_broken_module():
    bad = (
        "def test_a(page):\n"
        '    page.click(get_by_role("button", name="x").first)\n'
        "    page.click(e1)\n"
    )
    issues = validate_playwright_code(bad)
    assert any("get_by" in i for i in issues)          # bare get_by_*
    assert any("e1" in i for i in issues)              # leftover exploration ref
    assert any("import" in i.lower() for i in issues)  # missing playwright import


def test_validate_playwright_code_flags_syntax_error():
    assert any("SyntaxError" in i for i in validate_playwright_code("def f(:\n  pass"))


def test_model_family():
    assert model_family("qwen2.5-coder:7b") == "qwen"
    assert model_family("qwen2.5:14b") == "qwen"
    assert model_family("llama3.1:8b") == "llama"
    assert model_family("gpt-4o") == "gpt"


def test_same_model_family_flags_in_family_judge():
    assert same_model_family("qwen2.5-coder:7b", "qwen2.5:14b") is True
    assert same_model_family("qwen2.5-coder:7b", "llama3.1:8b") is False
    assert same_model_family("gpt-4o", "gpt-4o") is True


def test_extract_code_block_from_fence():
    text = "Here:\n```python\nprint('hi')\n```\ndone"
    assert extract_code_block(text) == "print('hi')"


def test_extract_code_block_without_fence_returns_text():
    assert extract_code_block("just code") == "just code"


def test_extract_json_object_strict():
    assert extract_json_object('{"action": "click", "ref": "e3"}') == {
        "action": "click", "ref": "e3"}


def test_extract_json_object_embedded():
    text = 'Sure. {"action": "navigate", "url": "/"} ok'
    assert extract_json_object(text) == {"action": "navigate", "url": "/"}


def test_extract_json_object_invalid_returns_empty():
    assert extract_json_object("no json here") == {}


def test_core_modules_import_without_heavy_deps():
    # These must import without playwright / deepeval / streamlit / ollama present,
    # proving the lazy-import boundaries hold.
    for mod in [
        "config.settings",
        "tcgen.orchestration.models",
        "tcgen.orchestration.experiment",
        "tcgen.orchestration.results_store",
        "tcgen.orchestration.aggregate",
        "tcgen.pipelines.crawler.serializer",
        "tcgen.pipelines.llm_agent.agent",
        "tcgen.pipelines.hybrid.refiner",
        "tcgen.runner.test_runner",
        "tcgen.runner.metrics.deepeval_judge",
        "tcgen.llm",
    ]:
        importlib.import_module(mod)
