"""Crawlee-based crawler backend (route discovery) — alternative to the BFS crawler.

Uses ``crawlee[playwright]`` as the crawl framework (request queue, autoscaling
concurrency, retries) with Chromium underneath, so it discovers JS-rendered SPA
routes fast and in parallel. It produces the SAME :class:`CrawlOutput` contract
as the BFS crawler, so the rest of the pipeline is unchanged.

Key differences from the BFS crawler (chosen deliberately):
* It DISCOVERS routes by following links and harvests every route's elements into
  the ``locator_catalog`` — including login/register (reached via their real
  ``#/…`` links, not seeded), which the click-based BFS crawler never reached.
* A bounded per-route INTERACTION PASS clicks non-link clickables and fills
  inputs (a pure link crawler is otherwise blind to everything behind a click:
  product dialogs, the search field, menus). Newly revealed elements enter the
  catalog, URL-changing results (``#/search?q=…``) are enqueued as routes.
* ``scenarios`` = the recorded interaction chains (replayable click/fill paths)
  plus route smokes for the remaining routes — so Skript_C exercises real
  affordances, comparable to the BFS baseline's click paths.

SPA hash routes (``#/login``) need explicit handling: most link crawlers treat a
``#/…`` change as a same-document fragment and never enqueue it. We therefore
harvest hash-route hrefs ourselves and enqueue each as its own request with an
explicit ``unique_key`` (the full URL incl. fragment) so they are not deduped away.

This backend is OPT-IN via ``TCGEN_CRAWLER_BACKEND=crawlee``; the BFS crawler
stays the default. ``crawlee`` is imported lazily so its absence never breaks the
default path.
"""

from __future__ import annotations

import asyncio
import re
import time
from urllib.parse import urljoin, urlparse

import networkx as nx

from config.settings import Settings, TargetApp, get_settings
from tcgen.pipelines.crawler.crawler import _SAMPLE_VALUES, CrawlOutput
from tcgen.pipelines.crawler.state import (
    HARVEST_JS,
    Action,
    ElementDescriptor,
    PageState,
    live_locator,
)
from tcgen.progress import NullPhase, Phase

# Never click controls that would mutate account state or leave the session;
# skip pure closers too ('Close search', 'Close Dialog') — with nothing open
# they only burn interaction budget.
_SKIP_NAME_RE = re.compile(
    r"(?i)\b(logout|log ?out|abmelden|delete|remove|löschen)\b|^close\b|^schlie(ß|ss)en\b")


def _fill_value(el: ElementDescriptor) -> str:
    """Sample value for an input (mirrors the BFS crawler's heuristics)."""
    hint = f"{el.type} {el.nameAttr} {el.placeholder} {el.ariaLabel} {el.id}".lower()
    if "search" in hint or "such" in hint:
        return _SAMPLE_VALUES["search"]
    if el.type in _SAMPLE_VALUES:
        return _SAMPLE_VALUES[el.type]
    if "mail" in hint:
        return _SAMPLE_VALUES["email"]
    if "pass" in hint:
        return _SAMPLE_VALUES["password"]
    return _SAMPLE_VALUES["text"]

# Collect same-app href targets (incl. SPA hash routes) so we can enqueue them
# explicitly — crawlers otherwise skip ``#/…`` fragments as same-document.
_HREF_JS = "() => [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'))"


class CrawleeCrawler:
    def __init__(self, target: TargetApp, settings: Settings | None = None):
        self.target = target
        self.settings = settings or get_settings()
        self._origin = self._origin_of(target.base_url)

    @staticmethod
    def _origin_of(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _same_app(self, url: str) -> bool:
        if self._origin_of(url) != self._origin:
            return False
        low = url.lower()
        # Same-origin redirect bouncers (Juice Shop's /redirect?to=https://github.com/…)
        # leave the app under test — off-task, and their TARGET page would otherwise be
        # recorded as a route and pollute catalog + completeness denominator.
        if "redirect?to=" in low or "/redirect?" in low:
            return False
        return not any(bad in low for bad in (self.target.avoid_url_substrings or []))

    def crawl(self, phase: Phase | None = None) -> CrawlOutput:
        """Sync entry point — runs the async Crawlee crawl to completion."""
        return asyncio.run(self._crawl_async(phase or NullPhase()))

    async def _crawl_async(self, phase: Phase) -> CrawlOutput:
        from crawlee import Request
        from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

        t0 = time.time()
        start_url = urljoin(self.target.base_url + "/",
                            self.target.entry_paths[0].lstrip("/"))
        states: dict[str, PageState] = {}   # url_key -> PageState
        nav_urls: dict[str, str] = {}       # url_key -> concrete navigable URL
        seen_reqs: set[str] = set()
        # Replayable interaction chains recorded by the per-route interaction
        # pass: (entry URL, [Action, ...]) -> serialised as real scenarios so
        # Skript_C exercises affordances (search, product dialogs), not only
        # route smokes.
        interactions: list[tuple[str, list[Action]]] = []

        crawler = PlaywrightCrawler(
            headless=self.settings.headless,
            max_requests_per_crawl=self.settings.crawler_max_states,
            browser_type="chromium",
        )

        async def _enqueue_url(context, url: str) -> None:
            if url in seen_reqs:
                return
            seen_reqs.add(url)
            try:
                await context.add_requests([Request.from_url(url, unique_key=url)])
            except Exception as exc:  # noqa: BLE001
                phase.log(f"  Enqueue fehlgeschlagen: {exc}")

        async def _interaction_pass(context, page, st: PageState) -> None:
            """Shallow, bounded interaction pass on a freshly discovered route.

            A pure link crawler never sees anything behind a CLICK — product
            dialogs, the search field (appears only after 'Open search'), menus.
            This pass clicks non-link clickables and fills inputs (search fields
            are submitted), then
            * merges newly revealed elements into the state (-> catalog/denominator),
            * enqueues URL-changing results (e.g. #/search?q=…) as new routes,
            * records each successful chain as a REPLAYABLE scenario so Skript_C
              exercises real affordances instead of only route smokes.
            """
            origin = page.url
            known = {e.signature() for e in st.elements}
            budget = max(1, self.settings.crawler_max_actions_per_state)
            done = 0
            # Snapshot: interact only with the route's ORIGINAL elements. Elements
            # merged from opened overlays are catalogued but not clicked — after
            # the Escape-reset they are gone (each click would just burn a
            # timeout), and e.g. language-menu radios would flip the UI language.
            # Prioritise (requirement-agnostic, purely UI-generic): search
            # controls first (mirrors the BFS crawler's is_search heuristic),
            # then FORM INPUTS (fields are the densest affordances on
            # login/register/contact pages), then named clickables, then
            # anonymous containers — so the bounded budget is not burned on
            # header buttons before any field was touched.
            def _prio(e: ElementDescriptor) -> int:
                name = (e.accessible_name or "").lower()
                if (e.is_input and e.is_search) or "search" in name or "such" in name:
                    return -1
                if e.is_input:
                    return 0
                return 1 if name.strip() else 2

            # One interaction per DISTINCT control: product grids repeat the
            # same named button ('Add to Basket') per card — clicking each
            # duplicate would burn the whole budget on one affordance.
            tried: set[str] = set()
            for el in sorted(st.elements, key=_prio):
                if done >= budget:
                    break
                name = el.accessible_name or ""
                if _SKIP_NAME_RE.search(name):
                    continue
                if el.role in ("radio", "option"):
                    continue
                sig = el.signature()
                if sig in tried:
                    continue
                tried.add(sig)
                try:
                    # Verify the semantic locator RESOLVES; if not (a11y name
                    # differs from the harvested aria-label, e.g. Juice Shop's
                    # 'Open search'), fall back to the exact CSS path — and mark
                    # the element so the serialised replay uses the same locator.
                    loc = live_locator(page, el)
                    if el.css and await loc.first.count() == 0:
                        el.prefer_css = True
                        loc = live_locator(page, el)
                    if el.is_input:
                        value = _fill_value(el)
                        await loc.first.fill(value, timeout=1200)
                        chain = [Action(kind="fill", element=el, value=value,
                                        submit=el.is_search)]
                        if el.is_search:
                            await loc.first.press("Enter", timeout=1200)
                            await page.wait_for_timeout(500)
                    elif el.tag != "a" and el.is_clickable:
                        # Same fallback the serialised script replays: normal
                        # click first, synthetic DOM click when actionability
                        # checks block it (ripple overlays, off-viewport).
                        try:
                            await loc.first.click(timeout=1200)
                        except Exception:  # noqa: BLE001
                            await loc.first.dispatch_event("click")
                        await page.wait_for_timeout(400)
                        chain = [Action(kind="click", element=el)]
                    else:
                        continue
                except Exception:  # noqa: BLE001 - exploration must be resilient
                    continue
                done += 1

                if page.url != origin:
                    # URL-changing control (search submit, tab switch): let the
                    # crawler visit the result as a first-class route.
                    if self._same_app(page.url):
                        interactions.append((origin, chain))
                        await _enqueue_url(context, page.url)
                    try:
                        await page.goto(origin)
                        await page.wait_for_timeout(300)
                    except Exception:  # noqa: BLE001
                        return
                    continue

                # Same route: an overlay/menu/dialog opened. Merge its elements
                # into the state so catalog + completeness denominator see them.
                try:
                    raw2 = await page.evaluate(HARVEST_JS)
                except Exception:  # noqa: BLE001
                    raw2 = []
                fresh: list[ElementDescriptor] = []
                for d in raw2:
                    el2 = ElementDescriptor(**d)
                    if el2.signature() not in known:
                        known.add(el2.signature())
                        st.elements.append(el2)
                        fresh.append(el2)
                # Chained search: 'Open search' reveals the input only now —
                # fill+submit immediately so #/search?q=… becomes a real route.
                search = next((e for e in fresh if e.is_input and e.is_search), None)
                if search is not None:
                    try:
                        sl = live_locator(page, search)
                        if search.css and await sl.first.count() == 0:
                            search.prefer_css = True
                            sl = live_locator(page, search)
                        await sl.first.fill(_SAMPLE_VALUES["search"], timeout=1200)
                        await sl.first.press("Enter", timeout=1200)
                        await page.wait_for_timeout(500)
                        chain = chain + [Action(kind="fill", element=search,
                                                value=_SAMPLE_VALUES["search"],
                                                submit=True)]
                        if page.url != origin and self._same_app(page.url):
                            await _enqueue_url(context, page.url)
                    except Exception:  # noqa: BLE001
                        pass
                # Only element-revealing or input chains are worth replaying.
                if fresh or chain[0].kind == "fill":
                    interactions.append((origin, chain))
                try:
                    await page.keyboard.press("Escape")
                except Exception:  # noqa: BLE001
                    pass
                if page.url != origin:
                    try:
                        await page.goto(origin)
                        await page.wait_for_timeout(300)
                    except Exception:  # noqa: BLE001
                        return
                else:
                    await page.wait_for_timeout(150)

        @crawler.router.default_handler
        async def handler(context: PlaywrightCrawlingContext) -> None:
            page = context.page
            # A same-origin request can REDIRECT out of the app (e.g. Juice Shop's
            # /redirect?to=github). Never record such a final page as a route —
            # its elements would pollute the catalog and the completeness
            # denominator with off-app content.
            if not self._same_app(page.url):
                phase.log(f"  übersprungen (verlässt die App): {page.url}")
                return
            # Pre-dismiss Juice Shop's welcome/cookie overlays so role-based
            # harvesting isn't blocked by an aria-hidden modal.
            try:
                await page.evaluate(
                    "() => { try { localStorage.setItem('welcomebanner_status','dismiss');"
                    " localStorage.setItem('cookieconsent_status','dismiss'); } catch(e){} }")
            except Exception:
                pass
            try:
                await page.wait_for_load_state("networkidle",
                                               timeout=self.settings.settle_timeout_ms)
            except Exception:
                pass

            # Harvest interactive elements (same JS as the BFS crawler).
            try:
                raw = await page.evaluate(HARVEST_JS)
            except Exception as exc:  # noqa: BLE001
                phase.log(f"  Harvest fehlgeschlagen auf {page.url}: {exc}")
                raw = []
            elements = [ElementDescriptor(**d) for d in raw]
            try:
                title = await page.title()
            except Exception:  # noqa: BLE001
                title = ""
            st = PageState(url=page.url, title=title, elements=elements)
            key = st.url_key
            if key not in states:
                states[key] = st
                nav_urls[key] = page.url
                phase.update(min(len(states) / max(self.settings.crawler_max_states, 1), 1.0),
                             f"Crawlee: {len(states)} Routen · {page.url}")
                # Go DEEPER than links can: click through the route's clickables
                # (product cards, 'Open search', menus) and fill its inputs.
                try:
                    await _interaction_pass(context, page, st)
                except Exception as exc:  # noqa: BLE001
                    phase.log(f"  Interaktions-Pass abgebrochen: {exc}")

            # Discover + enqueue same-app links, INCLUDING #/ hash routes, each with
            # an explicit unique_key so the fragment isn't deduped away.
            try:
                hrefs = await page.evaluate(_HREF_JS)
            except Exception:  # noqa: BLE001
                hrefs = []
            to_add = []
            for href in hrefs or []:
                if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                    continue
                full = urljoin(page.url, href)
                if not self._same_app(full) or full in seen_reqs:
                    continue
                seen_reqs.add(full)
                to_add.append(full)
            if to_add:
                # Request OBJECTS with an explicit unique_key (full URL incl. the
                # #/fragment). Plain dicts are rejected by add_requests (pydantic:
                # url/unique_key must be str — the dict lands in BOTH fields and
                # fails validation later inside crawler.run, past any try/except
                # here), and plain strings would dedupe every #/ hash route into
                # one request.
                try:
                    await context.add_requests(
                        [Request.from_url(u, unique_key=u) for u in to_add])
                except Exception as exc:  # noqa: BLE001
                    phase.log(f"  Enqueue fehlgeschlagen ({len(to_add)} Links): {exc}")

        seen_reqs.add(start_url)
        await crawler.run([start_url])

        # ---- assemble CrawlOutput ----
        catalog, routes, discovered = self._build_catalog(states)
        scenarios = self._scenarios(nav_urls, interactions)
        graph = nx.DiGraph()
        root = next(iter(states), None)
        for k in states:
            graph.add_node(k)
            if root and k != root:
                graph.add_edge(root, k)

        phase.update(1.0, f"Crawlee fertig: {len(states)} Routen, {discovered} Elemente, "
                          f"{len(scenarios)} Szenarien")
        return CrawlOutput(
            app_key=self.target.key,
            scenarios=scenarios,
            graph=graph,
            n_states=len(states),
            n_edges=graph.number_of_edges(),
            elapsed_s=round(time.time() - t0, 2),
            discovered_elements=discovered,
            locator_catalog=catalog,
            routes=routes,
        )

    def _link_stays_in_app(self, href: str) -> bool:
        """Whether an ``<a href>`` element belongs to the app under test.

        Filters footer/social links (GitHub, BlueSky, …), mailto/js anchors and
        redirect bouncers out of grounding and the completeness denominator —
        mirrors the BFS crawler's ``_followable_link``."""
        if not href or href.startswith(("javascript:", "mailto:", "tel:")):
            return False
        if href == "#" or (href.startswith("#") and len(href) <= 2):
            return False
        return self._same_app(urljoin(self.target.base_url + "/", href))

    def _build_catalog(self, states: dict[str, PageState], limit: int = 250):
        """Distinct robust (label, role, locator) catalog + routes + surface size.

        Uses the robust ``catalog_locator_code`` (text/role over brittle CSS), same
        as the BFS crawler. Returns ``(catalog, routes, n_distinct_locators)``: the
        catalog list is capped at ``limit`` for prompt size, while the distinct
        count is UNCAPPED and feeds ``discovered_elements`` — the completeness
        denominator, in the SAME unit as the exercised-locator numerator (counting
        raw element signatures instead inflates the denominator and pushed
        completeness below ~0.2)."""
        catalog: list[dict] = []
        seen: set[str] = set()
        for st in states.values():
            for el in st.elements:
                # Off-app links (external targets, redirect bouncers) never enter
                # grounding nor the denominator.
                if el.tag == "a" and not self._link_stays_in_app(el.href):
                    continue
                loc = el.catalog_locator_code("page")
                if loc in seen:
                    continue
                seen.add(loc)
                if len(catalog) < limit:
                    catalog.append({
                        "label": (el.accessible_name or el.text or el.tag)[:60],
                        "role": el.aria_role,
                        "locator": loc,
                        "url": st.url_key,
                    })
        routes = sorted(states.keys())
        return catalog, routes, len(seen)

    def _scenarios(self, nav_urls: dict[str, str],
                   interactions: list[tuple[str, list[Action]]]) -> list[list[Action]]:
        """Interaction chains first, route smokes fill the remainder.

        Interaction scenarios ([goto route, click/fill …]) exercise the app's
        real affordances (search, product dialogs, form fields) — they carry the
        element names story coverage checks for. Pure route smokes (goto + the
        serializer's body assertion) cover the remaining discovered routes."""
        limit = self.settings.crawler_max_scenarios
        # Dedupe by the chain's CONTROLS (the same 'Open Sidenav' exists on every
        # route — one replay suffices), then rank deterministically: chains with
        # NAMED elements before anonymous fills, longer chains (e.g. Open search
        # -> fill -> submit) before single clicks. Without this the selection
        # depends on the concurrent recording order and the cap can evict the
        # valuable chains.
        uniq: list[tuple[str, list[Action]]] = []
        seen: set[tuple] = set()
        for origin, chain in interactions:
            sig = tuple(a.element.signature() if a.element else a.url for a in chain)
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append((origin, chain))

        def _rank(oc: tuple[str, list[Action]]) -> tuple[int, int]:
            _origin, chain = oc
            named = any((a.element.accessible_name or "").strip()
                        for a in chain if a.element is not None)
            return (0 if named else 1, -len(chain))

        uniq.sort(key=_rank)  # stable: keeps recording order within a rank
        scenarios: list[list[Action]] = []
        for origin, chain in uniq:
            scenarios.append([Action(kind="goto", url=origin)] + chain)
            if len(scenarios) >= limit:
                return scenarios
        for url in nav_urls.values():
            if len(scenarios) >= limit:
                break
            scenarios.append([Action(kind="goto", url=url)])
        return scenarios
