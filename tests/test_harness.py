"""The shared pytest harness (conftest) the runner writes must be valid Python."""

from tcgen.runner.test_runner import _CONFTEST_TEMPLATE


def test_conftest_template_formats_and_compiles():
    source = _CONFTEST_TEMPLATE.format(timeout=15000)
    compile(source, "<conftest>", "exec")  # must be syntactically valid
    assert "set_default_timeout(15000)" in source
    # overlays are dismissed via Playwright's engine hook, not a goto monkeypatch
    assert "add_locator_handler" in source
    assert "page.goto =" not in source
