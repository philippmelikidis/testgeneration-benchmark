"""Browser backend for the LLM agent built on the **official Playwright MCP**
server (``@playwright/mcp``).

Instead of driving Playwright in-process via a bespoke harness, the agent now
explores through the standard Microsoft Playwright MCP server, talking to it over
the Model Context Protocol (JSON-RPC on stdio). This is the realistic, off-the-
shelf tool surface an LLM agent would use in practice, and the accessibility
*snapshot* it returns (an ARIA tree with stable ``[ref=eNN]`` element references)
is a stronger grounding signal than a hand-rolled DOM harvest.

Design:
* The agent keeps its portable JSON action protocol (navigate/click/fill/...),
  so small local Ollama models still work — we do NOT require native
  function-calling. This module merely *translates* those actions into MCP tool
  calls (``browser_navigate`` / ``browser_click`` / ``browser_type`` /
  ``browser_snapshot``).
* :class:`PlaywrightMcpSession` mirrors the API of the in-process
  ``BrowserSession`` (navigate/click/fill/get_text/observe + ``page.url``) so the
  agent loop is backend-agnostic.
* :func:`parse_snapshot` is a pure function (no I/O) and is unit-tested; the
  network/subprocess parts degrade gracefully and the agent falls back to the
  in-process backend if the MCP server cannot be started.

Requires Node.js 18+ on PATH (``npx``). Nothing is installed eagerly; the server
is launched on demand via ``npx @playwright/mcp@latest``.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

log = logging.getLogger(__name__)

# A line of an accessibility snapshot that carries an actionable element ref, e.g.
#   - textbox "What needs to be done?" [ref=e5]
#   - button "Add to Basket" [ref=e12] [cursor=pointer]
#   - link "Home" [ref=e3]
_SNAP_RE = re.compile(
    r'^\s*-\s+(?P<role>[\w-]+)'          # role, e.g. button / textbox / link
    r'(?:\s+"(?P<name>(?:[^"\\]|\\.)*)")?'  # optional quoted accessible name
    r'[^\n]*?\[ref=(?P<ref>e\d+)\]'      # the element reference
)
_URL_RE = re.compile(r'(?im)^\s*-?\s*Page URL:\s*(\S+)')
_TITLE_RE = re.compile(r'(?im)^\s*-?\s*Page Title:\s*(.+?)\s*$')


@dataclass
class SnapshotEl:
    """One actionable element extracted from a Playwright MCP snapshot."""

    ref: str
    role: str
    name: str = ""

    @property
    def description(self) -> str:
        """Human-readable element description (required by browser_click/type)."""
        return f'{self.role} "{self.name}"' if self.name else self.role


def parse_snapshot(text: str) -> list[SnapshotEl]:
    """Extract actionable elements (those with a ``[ref=eNN]``) from snapshot text.

    Robust to formatting drift: it scans every line for the ``[ref=...]`` marker
    regardless of indentation or surrounding YAML structure, and de-duplicates by
    ref (first occurrence wins).
    """
    out: list[SnapshotEl] = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = _SNAP_RE.search(line)
        if not m:
            continue
        ref = m.group("ref")
        if ref in seen:
            continue
        seen.add(ref)
        name = (m.group("name") or "").replace('\\"', '"').strip()
        out.append(SnapshotEl(ref=ref, role=m.group("role"), name=name))
    return out


def snapshot_url(text: str) -> str:
    m = _URL_RE.search(text)
    return m.group(1) if m else ""


def snapshot_title(text: str) -> str:
    m = _TITLE_RE.search(text)
    return m.group(1) if m else ""


class MCPError(RuntimeError):
    """Raised when the MCP server cannot be started or a call fails."""


class MCPClient:
    """Minimal JSON-RPC-over-stdio client for an MCP server subprocess.

    Implements just enough of the protocol for tool use: ``initialize`` handshake
    plus ``tools/call``. Messages are newline-delimited JSON (the MCP stdio
    transport). A background thread drains stdout so reads never deadlock.
    """

    PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, command: str, args: list[str], *, start_timeout_s: float = 60.0):
        self.command = command
        self.args = args
        self.start_timeout_s = start_timeout_s
        self._proc: subprocess.Popen | None = None
        self._q: "queue.Queue[dict]" = queue.Queue()
        self._reader: threading.Thread | None = None
        self._id = 0

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        exe = shutil.which(self.command)
        if not exe:
            raise MCPError(f"{self.command!r} not found on PATH (Node.js 18+ required)")
        try:
            self._proc = subprocess.Popen(
                [exe, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                # Own process group so close() can kill the server AND the browser
                # it spawns. Without this, hundreds of overnight runs would leak
                # chromium processes and exhaust memory.
                start_new_session=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise MCPError(f"failed to launch MCP server: {exc}") from exc

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

        # Handshake. The first response can be slow (npx may download the package).
        self._request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "tcgen-agent", "version": "0.1"},
        }, timeout=self.start_timeout_s)
        self._notify("notifications/initialized")

    def _read_loop(self) -> None:
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._q.put(json.loads(line))
            except json.JSONDecodeError:
                continue  # server diagnostic noise on stdout — ignore

    # ------------------------------------------------------------------ #
    def _write(self, msg: dict) -> None:
        if not self._proc or not self._proc.stdin:
            raise MCPError("MCP server not running")
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

    def _notify(self, method: str, params: dict | None = None) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _request(self, method: str, params: dict, *, timeout: float = 60.0) -> dict:
        self._id += 1
        rid = self._id
        self._write({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise MCPError(f"timeout waiting for response to {method!r}")
            try:
                msg = self._q.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self._proc and self._proc.poll() is not None:
                    raise MCPError("MCP server exited unexpectedly")
                continue
            if msg.get("id") != rid:
                continue  # notification or unrelated message
            if "error" in msg:
                raise MCPError(f"{method} error: {msg['error']}")
            return msg.get("result", {})

    # ------------------------------------------------------------------ #
    def call_tool(self, name: str, arguments: dict, *, timeout: float = 60.0) -> str:
        """Call an MCP tool and return its text content concatenated."""
        result = self._request("tools/call",
                               {"name": name, "arguments": arguments}, timeout=timeout)
        parts = []
        for item in result.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        if not parts:
            # Fall back to whatever the server returned so nothing is silently lost
            # (some servers put the snapshot under structuredContent or non-text).
            sc = result.get("structuredContent")
            if sc:
                parts.append(json.dumps(sc, ensure_ascii=False))
            elif result:
                parts.append(json.dumps(result, ensure_ascii=False))
        return "\n".join(parts)

    def close(self) -> None:
        if self._proc:
            # Kill the whole process group (server + chromium it spawned), not
            # just the node process, so no browser leaks across many runs.
            try:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    self._proc.terminate()
                except Exception:  # noqa: BLE001
                    pass
            try:
                self._proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                try:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)
                except Exception:  # noqa: BLE001
                    try:
                        self._proc.kill()
                    except Exception:  # noqa: BLE001
                        pass
        self._proc = None


class _PageShim:
    """Exposes ``.url`` so the agent loop can read it backend-agnostically."""

    def __init__(self) -> None:
        self.url = ""


class PlaywrightMcpSession:
    """Agent browser backend backed by the official Playwright MCP server.

    API-compatible with the in-process ``BrowserSession`` (navigate/click/fill/
    get_text/observe + ``.page.url`` + ``.ref_map``), so the agent loop does not
    care which backend it drives.
    """

    DEFAULT_ARGS = ["@playwright/mcp@latest", "--headless", "--isolated",
                    "--browser", "chromium"]

    def __init__(self, base_url: str, *, headless: bool = True, timeout_ms: int = 8000,
                 settle_timeout_ms: int = 1500, settle_pause_ms: int = 400,
                 command: str = "npx", args: list[str] | None = None,
                 start_timeout_s: float = 90.0, max_elements: int = 60):
        self.base_url = base_url
        self.max_elements = max_elements
        # settle_* are accepted for signature parity; Playwright MCP manages waits.
        args = list(args) if args is not None else list(self.DEFAULT_ARGS)
        if not headless and "--headless" in args:
            args.remove("--headless")
        self._client = MCPClient(command, args, start_timeout_s=start_timeout_s)
        self.page = _PageShim()
        self.ref_map: dict[str, SnapshotEl] = {}
        self._last_snapshot = ""

    # ------------------------------------------------------------------ #
    def __enter__(self) -> "PlaywrightMcpSession":
        self._client.start()
        return self

    def __exit__(self, *exc) -> None:
        self._client.close()

    # ------------------------------------------------------------------ #
    # tools (mirror BrowserSession)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _origin(url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _same_origin(self, url: str) -> bool:
        return self._origin(url) == self._origin(self.base_url)

    def navigate(self, url: str) -> str:
        target = urljoin(self.base_url + "/", url.lstrip("/")) if not url.startswith("http") else url
        note = ""
        # Keep the agent on the system under test: redirect any off-origin
        # navigation (e.g. a model wandering to google.com) back to the target.
        if not self._same_origin(target):
            note = (f"NOTE: '{url}' is outside the target application "
                    f"({self._origin(self.base_url)}). Navigation was kept on the "
                    f"target — only explore the target app.\n")
            target = self.base_url
        # Perform the navigation, then take an EXPLICIT snapshot: browser_navigate
        # does not reliably return the full accessibility tree, so relying on its
        # result left the agent with no element refs -> it could only navigate,
        # never click (the endless "navigate to base" loop). browser_snapshot
        # always returns the current tree with refs.
        self._client.call_tool("browser_navigate", {"url": target})
        return note + self.observe()

    def click(self, ref: str) -> str:
        el = self._lookup(ref)
        self._client.call_tool(
            "browser_click", {"element": el.description, "ref": ref})
        return self.observe()

    def fill(self, ref: str, value: str) -> str:
        el = self._lookup(ref)
        # Submit search fields (role searchbox / "search" in the name) so the
        # agent reaches result/detail states, mirroring the crawler. Other inputs
        # (login, registration) are filled without an implicit Enter.
        hint = f"{el.role} {el.name}".lower()
        submit = el.role == "searchbox" or "search" in hint or "such" in hint
        args = {"element": el.description, "ref": ref, "text": value}
        if submit:
            args["submit"] = True
        self._client.call_tool("browser_type", args)
        return self.observe()

    def get_text(self) -> str:
        # The accessibility snapshot already carries the page's visible text; the
        # in-process backend returned body innerText, so reuse the latest snapshot.
        return self._last_snapshot[:1500]

    def observe(self) -> str:
        text = self._client.call_tool("browser_snapshot", {})
        if not parse_snapshot(text):
            # Surface the real format so the parser can be fixed precisely instead
            # of guessed. Appears in the job's proc.log.
            log.warning("Playwright MCP snapshot yielded 0 parseable elements. "
                        "Raw result (first 800 chars):\n%s", (text or "")[:800])
        return self._ingest(text)

    # ------------------------------------------------------------------ #
    def _ingest(self, snapshot_text: str) -> str:
        """Parse an MCP tool result into ref_map + the agent's observation format."""
        self._last_snapshot = snapshot_text
        url = snapshot_url(snapshot_text)
        if url:
            self.page.url = url
        title = snapshot_title(snapshot_text)
        els = parse_snapshot(snapshot_text)[: self.max_elements]
        self.ref_map = {el.ref: el for el in els}
        self.last_element_count = len(els)
        lines = [f"URL: {self.page.url}", f"TITLE: {title}", "ELEMENTS:"]
        for el in els:
            # Omit the name when absent (no "(unnamed)" placeholder the model would
            # copy verbatim as a literal name).
            lines.append(f'  [{el.ref}] {el.role} "{el.name}"' if el.name
                         else f'  [{el.ref}] {el.role}')
        return "\n".join(lines)

    def _lookup(self, ref: str) -> SnapshotEl:
        if ref not in self.ref_map:
            raise KeyError(f"Unknown element ref: {ref!r}")
        return self.ref_map[ref]
