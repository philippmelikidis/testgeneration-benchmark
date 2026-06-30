"""State abstraction and action model for the crawler.

A *state* is an abstraction of a page: its normalised URL plus a stable
signature of the actionable elements it exposes. Two pages that lead to the same
set of interactions collapse to the same state, which keeps the state graph
finite on dynamic apps.

An *action* is a single interaction (click / fill / goto). The same Action
object is both *applied* to a live page during crawling and *rendered* to
Playwright-Python source during serialisation, guaranteeing that the emitted
script reproduces exactly what the crawler explored.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from urllib.parse import urlparse

# JavaScript run in the page to harvest candidate interactable elements.
# Returns a JSON-serialisable list of descriptors.
HARVEST_JS = r"""
() => {
  const cssFor = (el) => {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && parts.length < 5) {
      if (node.id) { parts.unshift('#' + CSS.escape(node.id)); break; }
      let part = node.tagName.toLowerCase();
      const parent = node.parentElement;
      if (parent) {
        const sameTag = Array.from(parent.children)
          .filter(c => c.tagName === node.tagName);
        if (sameTag.length > 1) {
          part += ':nth-of-type(' + (sameTag.indexOf(node) + 1) + ')';
        }
      }
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(' > ');
  };
  const out = [];
  // Semantically interactive elements (links, buttons, form fields) PLUS
  // generic clickable elements common in SPAs (ARIA roles, tabindex). Framework
  // widgets such as Angular Material product cards are <div>/<mat-card> with a
  // click handler and no semantic tag, so a second, style-based pass below
  // (cursor:pointer) catches them without hard-coding any app-specific selector.
  const sels = [
    'a[href]', 'button', 'input', 'select', 'textarea', '[onclick]',
    '[role="button"]', '[role="link"]', '[role="menuitem"]', '[role="tab"]',
    '[role="option"]', '[role="checkbox"]', '[role="radio"]', '[tabindex]',
  ].join(', ');
  const nodeSet = new Set(document.querySelectorAll(sels));
  // Style-based pass: generic containers the browser renders as clickable.
  for (const el of document.querySelectorAll(
        'div, span, li, mat-card, article, section')) {
    if (nodeSet.has(el)) continue;
    const cs = window.getComputedStyle(el);
    if (cs.cursor !== 'pointer') continue;
    const t = (el.innerText || '').trim();
    if (!t || t.length > 80) continue;   // skip empty/huge wrappers
    nodeSet.add(el);
  }
  const seen = new Set();
  const nodes = Array.from(nodeSet);
  for (const el of nodes) {
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    const visible = rect.width > 0 && rect.height > 0 &&
                    style.visibility !== 'hidden' && style.display !== 'none';
    if (!visible) continue;
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || '').toLowerCase();
    const text = (el.innerText || el.value || '').trim().slice(0, 80);
    const desc = {
      tag,
      type,
      text,
      id: el.id || '',
      nameAttr: el.getAttribute('name') || '',
      role: el.getAttribute('role') || '',
      ariaLabel: el.getAttribute('aria-label') || '',
      placeholder: el.getAttribute('placeholder') || '',
      testid: el.getAttribute('data-testid') || el.getAttribute('data-test') || '',
      href: el.getAttribute('href') || '',
      css: cssFor(el),
    };
    const key = [tag, type, desc.text, desc.id, desc.nameAttr, desc.href, desc.css].join('|');
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(desc);
  }
  return out;
}
"""


@dataclass
class ElementDescriptor:
    """A single actionable element, harvested from the DOM."""

    tag: str
    type: str = ""
    text: str = ""
    id: str = ""
    nameAttr: str = ""
    role: str = ""
    ariaLabel: str = ""
    placeholder: str = ""
    testid: str = ""
    href: str = ""
    css: str = ""  # unique-ish CSS path (id or nth-of-type chain) computed in JS

    # --- classification ---
    @property
    def is_input(self) -> bool:
        if self.tag == "textarea":
            return True
        if self.tag == "input":
            return self.type in ("", "text", "email", "search", "tel", "url", "password", "number")
        return False

    @property
    def is_submit(self) -> bool:
        return self.tag == "button" or (self.tag == "input" and self.type in ("submit", "button"))

    @property
    def is_clickable(self) -> bool:
        """Whether a click is a sensible interaction for this element.

        Covers semantic controls (buttons, links, ARIA button/link/menuitem/tab/
        option/checkbox/radio) and the generic clickable containers harvested via
        the cursor:pointer pass (SPA cards/tiles). Form text inputs and ``select``
        are excluded — they are handled as fills, not clicks."""
        if self.is_submit or self.tag == "a":
            return True
        if self.role in ("button", "link", "menuitem", "tab", "option",
                         "checkbox", "radio", "switch", "menuitemcheckbox"):
            return True
        # Anything else that made it into the harvest did so because it is
        # interactive (cursor:pointer / tabindex / onclick); treat as clickable,
        # except plain form fields handled elsewhere.
        return self.tag not in ("input", "select", "textarea")

    @property
    def is_search(self) -> bool:
        hint = f"{self.type} {self.nameAttr} {self.placeholder} {self.ariaLabel} {self.id}".lower()
        return self.type == "search" or "search" in hint or "such" in hint

    @property
    def aria_role(self) -> str:
        """Best-effort ARIA role for Playwright ``get_by_role``."""
        if self.role:
            return self.role
        if self.tag == "a":
            return "link"
        if self.is_submit:
            return "button"
        if self.tag == "select":
            return "combobox"
        if self.is_input:
            return "textbox"
        return "generic"

    @property
    def accessible_name(self) -> str:
        return (self.ariaLabel or self.text or self.placeholder or self.nameAttr).strip()

    def signature(self) -> str:
        return f"{self.tag}:{self.type}:{self.aria_role}:{self.accessible_name[:40]}:{self.href}"

    # --- Playwright-Python locator rendering ---
    def locator_code(self, page: str = "page") -> str:
        """Return a robust Playwright-Python locator expression as source code."""
        if self.testid:
            return f'{page}.get_by_test_id({_q(self.testid)})'
        name = self.accessible_name
        if self.is_input:
            if self.placeholder:
                return f'{page}.get_by_placeholder({_q(self.placeholder)})'
            if name:
                return f'{page}.get_by_role("textbox", name={_q(name)})'
        if name and self.aria_role != "generic":
            return f'{page}.get_by_role({_q(self.aria_role)}, name={_q(name)}).first'
        if self.id:
            return f'{page}.locator({_q("#" + self.id)})'
        if self.nameAttr:
            return f'{page}.locator({_q(f"[name={self.nameAttr!r}]")})'
        # Prefer the precise CSS path (matches the exact harvested element) over
        # text/tag fallbacks, which can select a different node on replay.
        if self.css:
            return f'{page}.locator({_q(self.css)})'
        if self.text:
            return f'{page}.get_by_text({_q(self.text)}, exact=False).first'
        # last resort
        return f'{page}.locator({_q(self.tag)}).first'


def _q(s: str) -> str:
    """Quote a string for embedding in generated Python source."""
    return json.dumps(s, ensure_ascii=False)


@dataclass
class Action:
    """A single interaction the crawler performed (and the script will replay)."""

    kind: str  # "goto" | "click" | "fill"
    element: ElementDescriptor | None = None
    value: str = ""          # for "fill"
    url: str = ""            # for "goto"
    # For "fill" on a search-like input: also press Enter to submit, so the
    # crawler reaches result/detail states instead of stopping at a typed-but-
    # never-submitted query (a common SPA dead end).
    submit: bool = False

    def describe(self) -> str:
        if self.kind == "goto":
            return f"goto {self.url}"
        name = self.element.accessible_name if self.element else "?"
        if self.kind == "fill":
            tail = " + Enter" if self.submit else ""
            return f"fill {name!r} = {self.value!r}{tail}"
        return f"click {name!r}"

    def code_lines(self, page: str = "page") -> list[str]:
        """Render this action to Playwright-Python source lines."""
        if self.kind == "goto":
            return [f"{page}.goto({_q(self.url)})", f"{page}.wait_for_load_state()"]
        assert self.element is not None
        loc = self.element.locator_code(page)
        if self.kind == "fill":
            lines = [f"{loc}.fill({_q(self.value)})"]
            if self.submit:
                # Submit the query (Enter), then wait for the result render.
                lines.append(f"{loc}.press(\"Enter\")")
                lines.append(f"{page}.wait_for_load_state()")
            return lines
        # click with a viewport-robust fallback: a normal click first, then a
        # force click for elements Playwright reports as "outside of the viewport"
        # (sidenav/footer links in scroll containers) that would otherwise retry
        # until timeout. force=True skips the actionability/viewport checks without
        # waiting (a plain scroll_into_view_if_needed can itself time out).
        # Short timeout on the normal click so a blocked element falls back fast
        # instead of burning the full per-action timeout (×tests ×flakiness =
        # minutes). Fallback dispatches a synthetic DOM click, which works even
        # for elements Playwright reports as "outside of the viewport" (force=True
        # still clicks by coordinate and fails for genuinely off-screen elements).
        return [
            "try:",
            f"    {loc}.click(timeout=2500)",
            "except Exception:",
            f"    {loc}.dispatch_event(\"click\")",
            f"{page}.wait_for_load_state()",
        ]


def normalise_url(url: str) -> str:
    """Collapse a URL to a state-relevant key.

    Includes the hash *route* (``#/foo``) because single-page apps encode their
    navigation there; without it every SPA route would collapse to one state.
    """
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    # Keep only structural query keys (drop volatile values).
    query_keys = sorted({kv.split("=")[0] for kv in p.query.split("&") if kv})
    key = f"{p.scheme}://{p.netloc}{path}"
    frag_route = p.fragment.split("?")[0].rstrip("/")
    if frag_route:
        key += f"#{frag_route}"
    return f"{key}?{','.join(query_keys)}"


def dismiss_overlays(page) -> None:
    """Best-effort: close common welcome dialogs / cookie banners blocking clicks.

    Generic across apps; silently ignores anything not present. Needed for SPAs
    like Juice Shop whose modal overlay otherwise intercepts every click.
    """
    import re

    attempts = []
    try:
        attempts.append(page.get_by_label("Close Welcome Banner"))
    except Exception:  # noqa: BLE001
        pass
    for name in ("Me want it!", "Dismiss"):
        try:
            attempts.append(page.get_by_text(name, exact=False))
        except Exception:  # noqa: BLE001
            pass
    try:
        attempts.append(page.get_by_role(
            "button", name=re.compile(r"(?i)\b(dismiss|got it|accept|agree|close|ok)\b")))
    except Exception:  # noqa: BLE001
        pass
    for loc in attempts:
        try:
            target = loc.first
            if target.count() > 0 and target.is_visible():
                target.click(timeout=1200)
                page.wait_for_timeout(200)
        except Exception:  # noqa: BLE001
            continue


def live_locator(page, el: "ElementDescriptor"):
    """Build a live Playwright locator from a descriptor (mirrors ``locator_code``).

    Shared by the crawler (replay) and the LLM agent (tool execution) so both
    target elements identically.
    """
    if el.testid:
        return page.get_by_test_id(el.testid)
    name = el.accessible_name
    if el.is_input:
        if el.placeholder:
            return page.get_by_placeholder(el.placeholder)
        if name:
            return page.get_by_role("textbox", name=name)
    if name and el.aria_role != "generic":
        return page.get_by_role(el.aria_role, name=name).first
    if el.id:
        return page.locator(f"#{el.id}")
    if el.nameAttr:
        return page.locator(f"[name={el.nameAttr!r}]")
    if el.css:
        return page.locator(el.css)
    if el.text:
        return page.get_by_text(el.text, exact=False).first
    return page.locator(el.tag).first


@dataclass
class PageState:
    """An abstracted page: normalised URL + signature of its actionable elements."""

    url: str
    title: str
    elements: list[ElementDescriptor] = field(default_factory=list)

    @property
    def url_key(self) -> str:
        return normalise_url(self.url)

    def signature(self) -> str:
        elem_sig = "|".join(sorted(e.signature() for e in self.elements))
        digest = hashlib.sha1(elem_sig.encode("utf-8")).hexdigest()[:12]
        return f"{self.url_key}#{digest}"
