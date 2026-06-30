"""Crawler exploration improvements: search submit + clickable classification."""

from tcgen.pipelines.crawler.state import HARVEST_JS, Action, ElementDescriptor


def test_search_fill_presses_enter():
    el = ElementDescriptor(tag="input", type="text", id="searchQuery",
                           placeholder="Search...")
    assert el.is_search is True
    act = Action(kind="fill", element=el, value="MacBook", submit=True)
    lines = act.code_lines()
    assert any('.fill("MacBook")' in ln for ln in lines)
    assert any('.press("Enter")' in ln for ln in lines)
    assert "Enter" in act.describe()


def test_non_search_fill_does_not_submit():
    el = ElementDescriptor(tag="input", type="email", id="email")
    assert el.is_search is False
    act = Action(kind="fill", element=el, value="a@b.de", submit=False)
    lines = act.code_lines()
    assert not any(".press(" in ln for ln in lines)


def test_generic_spa_card_is_clickable():
    # Angular Material card / generic clickable container.
    assert ElementDescriptor(tag="mat-card", text="Apple Juice").is_clickable is True
    assert ElementDescriptor(tag="div", role="menuitem", text="Account").is_clickable is True
    assert ElementDescriptor(tag="button", text="Add").is_clickable is True
    assert ElementDescriptor(tag="a", href="/x").is_clickable is True


def test_form_fields_are_not_clickable():
    assert ElementDescriptor(tag="input", type="text").is_clickable is False
    assert ElementDescriptor(tag="select").is_clickable is False
    assert ElementDescriptor(tag="textarea").is_clickable is False


def test_harvest_js_targets_generic_clickables():
    # The harvest must look beyond semantic tags (cursor:pointer + roles) so SPA
    # cards/dialog openers are discovered, not just <a>/<button>/<input>.
    assert "cursor" in HARVEST_JS
    assert "mat-card" in HARVEST_JS
    assert 'role="menuitem"' in HARVEST_JS
