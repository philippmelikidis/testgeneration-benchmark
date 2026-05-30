"""The shared pytest harness (conftest) the runner writes must be valid Python."""

from tcgen.runner.test_runner import _CONFTEST_TEMPLATE


def test_conftest_template_formats_and_compiles():
    source = _CONFTEST_TEMPLATE.format(timeout=8000)
    compile(source, "<conftest>", "exec")  # must be syntactically valid
    assert "set_default_timeout(8000)" in source
    assert "_dismiss_overlays" in source
    assert "page.goto = _goto" in source
