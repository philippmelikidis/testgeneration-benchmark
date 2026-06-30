"""Playwright MCP backend: snapshot parsing (pure, no subprocess needed)."""

from tcgen.pipelines.llm_agent.playwright_mcp import (
    SnapshotEl,
    parse_snapshot,
    snapshot_title,
    snapshot_url,
)

SNAP = '''### Ran Playwright code
- Page URL: http://localhost:3000/#/search
- Page Title: OWASP Juice Shop
- Page Snapshot:
```yaml
- banner:
  - button "Open Sidenav" [ref=e3] [cursor=pointer]
  - searchbox "Search" [ref=e5]
- main:
  - mat-card "Apple Juice (1000ml)" [ref=e21] [cursor=pointer]
  - link "Go to contact us page" [ref=e30]
  - text: plain text without a ref
  - generic [ref=e42]
```
'''


def test_parse_snapshot_extracts_refs_roles_names():
    els = parse_snapshot(SNAP)
    by_ref = {e.ref: e for e in els}
    assert set(by_ref) == {"e3", "e5", "e21", "e30", "e42"}
    assert by_ref["e5"].role == "searchbox"
    assert by_ref["e21"].name == "Apple Juice (1000ml)"
    assert by_ref["e42"].name == ""  # nameless element still captured by ref


def test_snapshot_skips_lines_without_ref():
    refs = {e.ref for e in parse_snapshot(SNAP)}
    assert "text: plain text without a ref" not in refs  # sanity: no junk refs


def test_snapshot_url_and_title():
    assert snapshot_url(SNAP) == "http://localhost:3000/#/search"
    assert snapshot_title(SNAP) == "OWASP Juice Shop"


def test_snapshot_element_description():
    assert SnapshotEl("e1", "button", "Login").description == 'button "Login"'
    assert SnapshotEl("e2", "generic", "").description == "generic"


def test_parse_snapshot_dedupes_by_ref():
    dup = SNAP + '\n- button "Open Sidenav" [ref=e3]\n'
    refs = [e.ref for e in parse_snapshot(dup)]
    assert refs.count("e3") == 1
