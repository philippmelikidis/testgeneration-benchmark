"""Live browser session exposed to the LLM agent as a small tool set.

Each observation re-harvests the current page's interactable elements and labels
them with stable refs (e1, e2, ...). The agent targets clicks/fills by ref,
which keeps it grounded in elements that actually exist (reducing hallucinated
selectors during *exploration* — the final synthesised script still uses the
model's own locators).
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from tcgen.pipelines.crawler.state import (
    HARVEST_JS,
    ElementDescriptor,
    dismiss_overlays,
    live_locator,
)


class BrowserSession:
    def __init__(self, base_url: str, *, headless: bool = True, timeout_ms: int = 8000,
                 settle_timeout_ms: int = 1500, settle_pause_ms: int = 400):
        self.base_url = base_url
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.settle_timeout_ms = settle_timeout_ms
        self.settle_pause_ms = settle_pause_ms
        self._pw = None
        self._browser = None
        self._ctx = None
        self.page = None
        self.ref_map: dict[str, ElementDescriptor] = {}

    def __enter__(self) -> "BrowserSession":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._ctx = self._browser.new_context()
        self.page = self._ctx.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        return self

    def __exit__(self, *exc) -> None:
        for closer in (self._ctx, self._browser):
            try:
                if closer:
                    closer.close()
            except Exception:  # noqa: BLE001
                pass
        if self._pw:
            self._pw.stop()

    # ------------------------------------------------------------------ #
    # tools
    # ------------------------------------------------------------------ #
    @staticmethod
    def _origin(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def navigate(self, url: str) -> str:
        target = urljoin(self.base_url + "/", url.lstrip("/")) if not url.startswith("http") else url
        note = ""
        # Keep the agent on the system under test: redirect off-origin
        # navigations (e.g. google.com) back to the target app.
        if self._origin(target) != self._origin(self.base_url):
            note = (f"NOTE: '{url}' is outside the target application "
                    f"({self._origin(self.base_url)}). Navigation was kept on the "
                    f"target — only explore the target app.\n")
            target = self.base_url
        self.page.goto(target)
        self._settle()
        dismiss_overlays(self.page)
        return note + self.observe()

    def click(self, ref: str) -> str:
        el = self._lookup(ref)
        live_locator(self.page, el).click()
        self._settle()
        return self.observe()

    def _settle(self) -> None:
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:  # noqa: BLE001
            pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=self.settle_timeout_ms)
        except Exception:  # noqa: BLE001
            pass
        self.page.wait_for_timeout(self.settle_pause_ms)

    def fill(self, ref: str, value: str) -> str:
        el = self._lookup(ref)
        live_locator(self.page, el).fill(value)
        return self.observe()

    def get_text(self) -> str:
        body = self.page.inner_text("body")
        return body[:1500]

    # ------------------------------------------------------------------ #
    # observation
    # ------------------------------------------------------------------ #
    def observe(self) -> str:
        raw = self.page.evaluate(HARVEST_JS)
        self.ref_map = {}
        lines = [f"URL: {self.page.url}", f"TITLE: {self.page.title()}", "ELEMENTS:"]
        for i, d in enumerate(raw[:60], start=1):
            el = ElementDescriptor(**d)
            ref = f"e{i}"
            self.ref_map[ref] = el
            lines.append(f"  [{ref}] {self._describe(el)}")
        return "\n".join(lines)

    def _describe(self, el: ElementDescriptor) -> str:
        kind = "input" if el.is_input else ("button" if el.is_submit else el.aria_role)
        name = el.accessible_name or el.placeholder or "(unnamed)"
        extra = f' href="{el.href}"' if el.href else ""
        return f'{kind} "{name}"{extra}'

    def _lookup(self, ref: str) -> ElementDescriptor:
        if ref not in self.ref_map:
            raise KeyError(f"Unknown element ref: {ref!r}")
        return self.ref_map[ref]
