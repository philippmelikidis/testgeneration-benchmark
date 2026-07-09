"""The shared pytest harness (conftest) the runner writes must be valid Python."""

from tcgen.runner.test_runner import _CONFTEST_TEMPLATE, _predismiss_js


def _render(predismiss=None):
    return _CONFTEST_TEMPLATE.format(
        timeout=15000,
        selectors=repr(["#dismissWelcomeButton", "a.cc-dismiss"]),
        predismiss_js=repr(_predismiss_js(predismiss or {})),
    )


def test_conftest_template_formats_and_compiles():
    source = _render({"welcomebanner_status": "dismiss"})
    compile(source, "<conftest>", "exec")  # must be syntactically valid
    assert "set_default_timeout(15000)" in source
    # overlays are dismissed via Playwright's engine hook, not a goto monkeypatch
    assert "add_locator_handler" in source
    assert "page.goto =" not in source
    # no regex-name locators (they raise InvalidSelectorError in Playwright)
    assert "re.compile" not in source
    assert "#dismissWelcomeButton" in source


def test_predismiss_comes_from_target_config_not_hardcoded():
    # App-specific pre-seed keys must come from the target YAML; a target
    # without predismiss config gets an empty (skipped) init script.
    js = _predismiss_js({"welcomebanner_status": "dismiss"})
    assert 'localStorage.setItem("welcomebanner_status","dismiss")' in js
    assert "document.cookie" in js
    assert _predismiss_js({}) == ""
    empty = _render()
    compile(empty, "<conftest>", "exec")
    assert "welcomebanner_status" not in empty  # nothing app-specific baked in
