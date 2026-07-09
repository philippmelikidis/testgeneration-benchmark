"""Autonomous Playwright crawler.

Explores a target app breadth-first, abstracting pages into states and
recording the action paths between them in a state graph. The selected paths are
handed to :mod:`tcgen.pipelines.crawler.serializer` to emit ``Skript_C``.

Design choices:
* **Incremental reach** exploration (fast): links are followed by navigating
  straight to their (SPA hash) target, and non-link states are re-established by
  a single ``goto`` to their URL — falling back to a full action-path replay only
  for states a URL cannot reproduce (open menus/dialogs, post-submit views). This
  keeps exploration deterministic and avoids fragile back-button handling on SPAs,
  while replacing the old O(states*depth) from-root replay (one navigation per
  candidate instead of one per path step). The recorded path stays click/fill-
  based, so ``Skript_C`` still reproduces real user interactions.
* The crawler is **requirement-agnostic** by design — that is precisely the
  traditional baseline the study contrasts against the LLM agent.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import networkx as nx

from config.settings import Settings, TargetApp, get_settings
from tcgen.progress import NullPhase, Phase
from tcgen.pipelines.crawler.state import (
    HARVEST_JS,
    Action,
    ElementDescriptor,
    PageState,
    dismiss_overlays,
    live_locator,
)

log = logging.getLogger(__name__)

# Values the crawler types into inputs it encounters.
_SAMPLE_VALUES = {
    "search": "MacBook",
    "email": "tester@example.com",
    "password": "Passw0rd!",
    "text": "Test",
    "tel": "1234567890",
    "number": "1",
}
@dataclass
class CrawlOutput:
    """Result of a crawl: graph, selected scenarios, and statistics."""

    app_key: str
    scenarios: list[list[Action]] = field(default_factory=list)
    graph: "nx.DiGraph" = field(default_factory=nx.DiGraph)
    n_states: int = 0
    n_edges: int = 0
    elapsed_s: float = 0.0
    # Distinct interactable elements found across ALL crawled states — the
    # "reachable surface" used as the denominator for completeness.
    discovered_elements: int = 0
    # Grounding for the hybrid (Skript_H): the REAL, verified locators the crawler
    # used (label/role/locator_code) and the distinct routes it reached. Passed to
    # the LLM so Skript_H can write story tests grounded in elements that actually
    # exist, instead of inventing selectors.
    locator_catalog: list[dict] = field(default_factory=list)
    routes: list[str] = field(default_factory=list)


class Crawler:
    def __init__(self, target: TargetApp, settings: Settings | None = None):
        self.target = target
        self.settings = settings or get_settings()
        self._origin = self._origin_of(target.base_url)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def crawl(self, phase: Phase | None = None) -> CrawlOutput:
        """Run the exploration and return the discovered scenarios."""
        from playwright.sync_api import sync_playwright

        phase = phase or NullPhase()
        max_states = self.settings.crawler_max_states
        t0 = time.time()
        graph = nx.DiGraph()
        states: dict[str, PageState] = {}
        # signature -> action path from root
        paths: dict[str, list[Action]] = {}

        # SINGLE root — identical starting point for every pipeline (crawler and
        # LLM agent alike), so the comparison stays fair: each strategy must
        # DISCOVER deeper states (login/register behind the account menu) by its
        # own autonomous exploration, none is hand-fed seeded entry points.
        start_url = urljoin(self.target.base_url + "/", self.target.entry_paths[0].lstrip("/"))
        root_path = [Action(kind="goto", url=start_url)]

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.settings.headless)
            ctx = browser.new_context()
            page = ctx.new_page()
            # Short per-action timeout during exploration so broken/blocked
            # candidate actions fail fast instead of stalling the whole crawl.
            page.set_default_timeout(self.settings.crawler_action_timeout_ms)

            phase.update(0.02, f"Crawler startet bei {start_url}")
            self._apply(page, root_path[0])  # actually navigate to the entry URL
            root_state = self._capture(page, root_path)
            root_sig = root_state.signature()
            phase.log(f"Root erfasst: {len(root_state.elements)} Elemente auf {root_state.url}")
            states[root_sig] = root_state
            paths[root_sig] = root_path
            graph.add_node(root_sig, url=root_state.url, title=root_state.title)

            budget_s = self.settings.crawler_time_budget_s
            frontier: list[tuple[str, int]] = [(root_sig, 0)]
            while frontier and len(states) < max_states:
                if budget_s and (time.time() - t0) > budget_s:
                    phase.log(f"Zeitbudget {budget_s}s erreicht — Crawl wird beendet "
                              f"({len(states)} Zustände)")
                    break
                sig, depth = frontier.pop(0)
                if depth >= self.settings.crawler_max_depth:
                    continue
                state = states[sig]
                candidates = self._candidate_actions(state)
                for i, action in enumerate(candidates, start=1):
                    if len(states) >= max_states:
                        break
                    if budget_s and (time.time() - t0) > budget_s:
                        break
                    # Stream per-action progress so a state with many candidates
                    # is visibly working, not "hung".
                    phase.log(f"  Zustand {len(states)} · Aktion {i}/{len(candidates)} "
                              f"· {action.describe()}")
                    new_path = paths[sig] + [action]
                    new_state = self._reach_via_action(page, state, paths[sig], action)
                    if new_state is None:
                        continue
                    nsig = new_state.signature()
                    graph.add_node(nsig, url=new_state.url, title=new_state.title)
                    graph.add_edge(sig, nsig, label=action.describe())
                    if nsig not in states:
                        states[nsig] = new_state
                        paths[nsig] = new_path
                        frontier.append((nsig, depth + 1))
                        phase.update(
                            len(states) / max_states,
                            f"Zustand {len(states)}/{max_states} · Tiefe {depth + 1} "
                            f"· {action.describe()}",
                        )

            ctx.close()
            browser.close()

        scenarios = self._select_scenarios(
            states, paths, root_sig, max_scenarios=self.settings.crawler_max_scenarios)
        discovered = len({e.signature() for st in states.values() for e in st.elements})
        catalog, routes = self._build_catalog(states)
        phase.update(1.0, f"Crawl fertig: {len(states)} Zustände, "
                          f"{graph.number_of_edges()} Übergänge, "
                          f"{len(scenarios)} Szenarien, {discovered} Elemente")
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

    def _build_catalog(self, states: dict[str, PageState], limit: int = 250):
        """Distinct (label, role, locator_code) catalog + distinct routes.

        The locator catalog is the crawler's REAL, verified element vocabulary —
        handed to the hybrid refiner so Skript_H grounds every locator in
        something that actually exists in the app. Off-task elements are filtered
        out: external links (e.g. the GitHub link) and avoided routes (score-board,
        admin, logout) — otherwise the grounded Skript_H may wander off the app
        (e.g. "search" on GitHub instead of in the shop)."""
        catalog: list[dict] = []
        seen: set[str] = set()
        for st in states.values():
            for el in st.elements:
                # Drop links the crawler would not follow (external origin,
                # mailto/tel, avoided substrings) so they never enter grounding.
                if el.tag == "a" and not self._followable_link(el.href):
                    continue
                # Robust, user-facing locator for GROUNDING (text/role over brittle
                # nth-of-type CSS) so Skript_H doesn't inherit fragile selectors.
                loc = el.catalog_locator_code("page")
                if loc in seen:
                    continue
                seen.add(loc)
                catalog.append({
                    "label": (el.accessible_name or el.text or el.tag)[:60],
                    "role": el.aria_role,
                    "locator": loc,
                    # Route where this element was first seen — lets the hybrid
                    # map a story to the RIGHT element (e.g. register fields on
                    # /#/register, not a look-alike on the feedback form).
                    "url": st.url_key,
                })
                if len(catalog) >= limit:
                    break
            if len(catalog) >= limit:
                break
        routes = sorted({st.url_key for st in states.values()})
        return catalog, routes

    # ------------------------------------------------------------------ #
    # exploration helpers
    # ------------------------------------------------------------------ #
    def _candidate_actions(self, state: PageState) -> list[Action]:
        """Pick a bounded, deduplicated set of interactions for a state."""
        actions: list[Action] = []
        seen: set[str] = set()
        for el in state.elements:
            if el.is_input:
                value = self._value_for(el)
                # Submit search-like fields so result/detail states are reached.
                act = Action(kind="fill", element=el, value=value, submit=el.is_search)
            elif el.tag == "a":
                if not self._followable_link(el.href):
                    continue
                act = Action(kind="click", element=el)
            elif el.is_clickable:
                act = Action(kind="click", element=el)
            else:
                continue
            key = el.signature() + act.kind + ("!" if act.submit else "")
            if key in seen:
                continue
            seen.add(key)
            actions.append(act)
            if len(actions) >= self.settings.crawler_max_actions_per_state:
                break
        return actions

    def _value_for(self, el: ElementDescriptor) -> str:
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

    def _followable_link(self, href: str) -> bool:
        if not href or href.startswith(("javascript:", "mailto:", "tel:")):
            return False
        # Bare "#" is a no-op anchor; "#/route" is internal SPA navigation (allow).
        if href == "#" or (href.startswith("#") and len(href) <= 2):
            return False
        # Same-origin redirect bouncers (e.g. Juice Shop's
        # /redirect?to=https://github.com/...) leave the app under test — off-task
        # and usually rendered off-screen in the sidenav. Skip them.
        if "redirect?to=" in href or "/redirect?" in href:
            return False
        absolute = urljoin(self.target.base_url + "/", href)
        if self._origin_of(absolute) != self._origin:
            return False
        if any(s in absolute for s in self.target.avoid_url_substrings):
            return False
        return True

    def _reach_via_action(self, page, state: PageState, state_path: list[Action],
                          action: Action) -> PageState | None:
        """Apply ``action`` from ``state`` and capture the resulting state — fast.

        Avoids the old O(depth) from-root replay for every candidate:

        * **Link** (``<a href>``): navigate straight to the link target. On an SPA
          a link click is equivalent to loading its hash route, so a single
          ``goto`` reaches the same DOM the click would — and the *next* link
          candidate is likewise a single ``goto`` (no separate restore step). The
          recorded action stays a ``click`` so ``Skript_C`` still clicks the link.
        * **Other** (button / fill / generic): cheaply restore the state (one
          ``goto`` to its URL, or a path replay as fallback for non-URL-addressable
          states such as an open menu/dialog), then apply the action.
        """
        try:
            el = action.element
            if action.kind == "click" and el is not None and el.tag == "a" and el.href:
                absolute = urljoin(self.target.base_url + "/", el.href)
                self._apply(page, Action(kind="goto", url=absolute))
                return self._capture(page, state_path + [action])
            if not self._restore(page, state, state_path):
                return None
            self._apply(page, action)
            return self._capture(page, state_path + [action])
        except Exception as exc:  # noqa: BLE001 - exploration must be resilient
            log.debug("Reach via %s failed: %s", action.describe(), exc)
            return None

    def _restore(self, page, state: PageState, state_path: list[Action]) -> bool:
        """Re-establish ``state`` on the live page before applying a non-link action.

        Tries the cheap path first — a direct ``goto`` to the state's URL — and
        verifies the element signature matches. Falls back to replaying the full
        action path for states that a URL alone cannot reproduce (open menus,
        dialogs, post-submit views)."""
        try:
            self._apply(page, Action(kind="goto", url=state.url))
            if self._capture(page, state_path).signature() == state.signature():
                return True
        except Exception:  # noqa: BLE001
            pass
        try:
            for a in state_path:
                self._apply(page, a)
            return self._capture(page, state_path).signature() == state.signature()
        except Exception as exc:  # noqa: BLE001
            log.debug("Restore failed for %s: %s", state.url, exc)
            return False

    def _apply(self, page, action: Action) -> None:
        if action.kind == "goto":
            page.goto(action.url)
            self._settle(page)
            dismiss_overlays(page)
            return
        locator = self._resolve(page, action.element)
        if action.kind == "fill":
            locator.fill(action.value)
            if action.submit:
                locator.press("Enter")
                self._settle(page)
        else:
            # Normal click only during exploration: a state reached via a
            # force/synthetic click often cannot be reproduced on replay, which
            # produces fragile scenarios. If a normal click fails the candidate is
            # simply skipped (caller catches), keeping recorded paths replayable.
            locator.click()
            self._settle(page)

    def _settle(self, page) -> None:
        """Wait for an SPA to finish rendering after a navigation/click."""
        try:
            page.wait_for_load_state("domcontentloaded")
        except Exception:  # noqa: BLE001
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=self.settings.settle_timeout_ms)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(self.settings.settle_pause_ms)  # let frameworks paint

    def _resolve(self, page, el: ElementDescriptor):
        return live_locator(page, el)

    def _capture(self, page, path: list[Action]) -> PageState:
        raw = page.evaluate(HARVEST_JS)
        elements = [ElementDescriptor(**d) for d in raw]
        return PageState(url=page.url, title=page.title(), elements=elements)

    # ------------------------------------------------------------------ #
    # scenario selection
    # ------------------------------------------------------------------ #
    def _select_scenarios(
        self,
        states: dict[str, PageState],
        paths: dict[str, list[Action]],
        root_sig: str,
        max_scenarios: int = 10,
    ) -> list[list[Action]]:
        """Choose a diverse set of root->state paths to serialise as tests.

        Preference: longer paths first (more interaction), one per distinct
        terminal URL key, always excluding the trivial root-only path.
        """
        candidates = [
            (sig, p) for sig, p in paths.items() if sig != root_sig and len(p) > 1
        ]
        candidates.sort(key=lambda sp: len(sp[1]), reverse=True)
        chosen: list[list[Action]] = []
        seen_terminals: set[str] = set()
        for sig, p in candidates:
            terminal = states[sig].url_key
            if terminal in seen_terminals:
                continue
            seen_terminals.add(terminal)
            chosen.append(p)
            if len(chosen) >= max_scenarios:
                break
        # Guarantee at least the homepage smoke path.
        if not chosen:
            chosen = [paths[root_sig]]
        return chosen

    @staticmethod
    def _origin_of(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"
