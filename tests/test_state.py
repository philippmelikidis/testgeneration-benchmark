from tcgen.pipelines.crawler.state import (
    Action,
    ElementDescriptor,
    PageState,
    normalise_url,
)


def test_link_locator_uses_role_and_name():
    el = ElementDescriptor(tag="a", text="Search", href="/search")
    assert el.aria_role == "link"
    assert el.locator_code() == 'page.get_by_role("link", name="Search").first'


def test_input_with_placeholder_locator():
    el = ElementDescriptor(tag="input", type="search", placeholder="Search")
    assert el.is_input
    assert el.locator_code() == 'page.get_by_placeholder("Search")'


def test_testid_takes_precedence():
    el = ElementDescriptor(tag="button", text="Go", testid="submit-btn")
    assert el.locator_code() == 'page.get_by_test_id("submit-btn")'


def test_css_fallback_for_unnamed_input():
    # An input with no testid/name/id/placeholder/text must fall back to the
    # precise CSS path, NOT locator("input").first (which can hit another node).
    el = ElementDescriptor(tag="input", css="form > input:nth-of-type(2)")
    assert el.locator_code() == 'page.locator("form > input:nth-of-type(2)")'


def test_named_link_still_prefers_role_over_css():
    # A link with visible text keeps the semantic role+name locator; css is only
    # a fallback for elements without a usable name.
    el = ElementDescriptor(tag="a", text="Search", href="/s", css="nav > a:nth-of-type(3)")
    assert el.locator_code() == 'page.get_by_role("link", name="Search").first'


def test_goto_action_code_lines():
    act = Action(kind="goto", url="http://localhost:8080/")
    assert act.code_lines() == [
        'page.goto("http://localhost:8080/")',
        "page.wait_for_load_state()",
    ]


def test_click_action_code_lines():
    el = ElementDescriptor(tag="a", text="Cart", href="/cart")
    act = Action(kind="click", element=el)
    lines = act.code_lines()
    assert any(".click()" in ln for ln in lines)
    assert "page.wait_for_load_state()" in lines


def test_fill_action_code_lines():
    el = ElementDescriptor(tag="input", type="search", placeholder="Search")
    act = Action(kind="fill", element=el, value="MacBook")
    assert act.code_lines() == ['page.get_by_placeholder("Search").fill("MacBook")']


def test_normalise_url_sorts_query_keys_and_strips_values():
    assert normalise_url("http://h/a/b/?y=2&x=1") == "http://h/a/b?x,y"
    assert normalise_url("http://h/") == "http://h/?"


def test_normalise_url_keeps_spa_hash_route():
    # SPA routes live in the fragment and must distinguish states
    assert normalise_url("http://h:3000/#/search") == "http://h:3000/#/search?"
    assert normalise_url("http://h:3000/#/") == "http://h:3000/?"
    assert (normalise_url("http://h:3000/#/search")
            != normalise_url("http://h:3000/#/login"))


def test_pagestate_signature_is_stable_and_order_independent():
    e1 = ElementDescriptor(tag="a", text="A", href="/a")
    e2 = ElementDescriptor(tag="a", text="B", href="/b")
    s1 = PageState(url="http://h/p", title="t", elements=[e1, e2])
    s2 = PageState(url="http://h/p", title="t", elements=[e2, e1])
    assert s1.signature() == s2.signature()
