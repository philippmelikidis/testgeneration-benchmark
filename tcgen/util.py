"""Small shared helpers."""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_code_block(text: str) -> str:
    """Return the first fenced code block, or the whole text if none is found."""
    m = _FENCE_RE.search(text)
    return (m.group(1) if m else text).strip()


def extract_json_object(text: str) -> dict:
    """Best-effort extraction of a single JSON object from model output.

    Tries strict parse first, then the first ``{...}`` span. Returns ``{}`` on
    failure so callers can decide how to recover.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # strip code fences if present
    block = extract_code_block(text)
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        pass
    m = _OBJ_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {}
    return {}


def truncate(s: str, limit: int = 2000) -> str:
    return s if len(s) <= limit else s[:limit] + "\n…[truncated]"


_BARE_GETBY_RE = re.compile(r"(?<![\.\w])get_by_\w+\s*\(")
_LEFTOVER_REF_RE = re.compile(r"\(\s*[a-z]\d+\s*\)")  # e.g. click(e1) — exploration ref


def validate_playwright_code(code: str) -> list[str]:
    """Return a list of problems that would make a pytest-playwright module fail.

    High-precision checks only (so we don't trigger needless repair rounds):
    syntax errors, ``get_by_*`` used without a ``page``/locator prefix, leftover
    exploration refs like ``click(e1)``, and a missing Playwright import.
    """
    issues: list[str] = []
    try:
        compile(code, "<skript_l>", "exec")
    except SyntaxError as exc:
        issues.append(f"SyntaxError: {exc.msg} (Zeile {exc.lineno})")
    if _BARE_GETBY_RE.search(code):
        issues.append("get_by_*() ohne page/locator-Präfix (z. B. page.get_by_role(...)).")
    if _LEFTOVER_REF_RE.search(code):
        issues.append("verweist auf undefinierte Explorations-Refs wie e1 (z. B. click(e1)).")
    if "from playwright.sync_api import" not in code:
        issues.append("fehlender Import: from playwright.sync_api import Page, expect")
    return issues


def model_family(model: str) -> str:
    """Leading alphabetic family of a model id, e.g. 'qwen2.5-coder' -> 'qwen'."""
    m = re.match(r"[a-zA-Z]+", model.strip())
    return m.group(0).lower() if m else ""


def same_model_family(a: str, b: str) -> bool:
    """True if two model ids share a family (e.g. generator and judge both Qwen).

    Used to flag potential LLM-as-judge in-family bias.
    """
    fa, fb = model_family(a), model_family(b)
    return bool(fa) and fa == fb
