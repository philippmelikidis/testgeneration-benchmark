"""Autonomous Playwright crawler.

Explores a target app breadth-first, abstracting pages into states and
recording the action paths between them in a state graph. The selected paths are
handed to :mod:`tcgen.pipelines.crawler.serializer` to emit ``Skript_C``.

Design choices:
* **Replay-from-root** exploration: to reach a state we replay its recorded
  action path in a fresh page. This is deterministic and avoids fragile
  back-button handling on SPAs, at the cost of O(states*depth) navigations,
  which is acceptable for the bounded state budget used in the study.
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

        start_url = urljoin(self.target.base_url + "/", self.target.entry_paths[0].lstrip("/"))
        root_path = [Action(kind="goto", url=start_url)]

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.settings.headless)
            ctx = browser.new_context()
            page = ctx.new_page()
            page.set_default_timeout(8000)

            phase.update(0.02, f"Crawler startet bei {start_url}")
            self._apply(page, root_path[0])  # actually navigate to the entry URL
            root_state = self._capture(page, root_path)
            root_sig = root_state.signature()
            phase.log(f"Root erfasst: {len(root_state.elements)} Elemente auf {root_state.url}")
            states[root_sig] = root_state
            paths[root_sig] = root_path
            graph.add_node(root_sig, url=root_state.url, title=root_state.title)

            frontier: list[tuple[str, int]] = [(root_sig, 0)]
            while frontier and len(states) < max_states:
                sig, depth = frontier.pop(0)
                if depth >= self.settings.crawler_max_depth:
                    continue
                state = states[sig]
                for action in self._candidate_actions(state):
                    if len(states) >= max_states:
                        break
                    new_path = paths[sig] + [action]
                    new_state = self._replay_and_capture(page, new_path)
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
        )

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
                act = Action(kind="fill", element=el, value=value)
            elif el.tag == "a":
                if not self._followable_link(el.href):
                    continue
                act = Action(kind="click", element=el)
            elif el.is_submit:
                act = Action(kind="click", element=el)
            else:
                continue
            key = el.signature() + act.kind
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
        absolute = urljoin(self.target.base_url + "/", href)
        if self._origin_of(absolute) != self._origin:
            return False
        if any(s in absolute for s in self.target.avoid_url_substrings):
            return False
        return True

    def _replay_and_capture(self, page, path: list[Action]) -> PageState | None:
        """Replay an action path from root in a fresh page; capture the result."""
        try:
            for action in path:
                self._apply(page, action)
            return self._capture(page, path)
        except Exception as exc:  # noqa: BLE001 - exploration must be resilient
            log.debug("Path replay failed (%s): %s", path[-1].describe() if path else "-", exc)
            return None

    def _apply(self, page, action: Action) -> None:
        if action.kind == "goto":
            page.goto(action.url)
            self._settle(page)
            dismiss_overlays(page)
            return
        locator = self._resolve(page, action.element)
        if action.kind == "fill":
            locator.fill(action.value)
        else:
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
