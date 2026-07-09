"""Small shared helpers."""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)
# Thinking models (glm-5.1, gpt-oss, deepseek, ...) may wrap reasoning in these.
_THINK_RE = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)


def _strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text)


def extract_code_block(text: str) -> str:
    """Return the first fenced code block, or the whole text if none is found.

    Reasoning blocks from thinking models are stripped first so they never leak
    into the extracted code.
    """
    text = _strip_thinking(text)
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
# Exploration ref leaked as a literal locator string, e.g. get_by_text("e1") or
# name="e3". Real app labels are virtually never exactly e<digits>.
_REF_AS_TEXT_RE = re.compile(r"""(?:get_by_\w+\(|name\s*=)\s*['"]e\d+['"]""")


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
    if _REF_AS_TEXT_RE.search(code):
        issues.append("nutzt einen Explorations-Ref als Locator-Text (z. B. "
                      'get_by_text("e1") / name="e3") — das ist kein echtes UI-Label.')
    if "from playwright.sync_api import" not in code:
        issues.append("fehlender Import: from playwright.sync_api import Page, expect")
    return issues


# Non-waiting `assert <loc>.count() > 0` / `>= 1` — a common LLM idiom for "at
# least one result". `.count()` returns immediately, so on async-rendered content
# (search results, product cards) it reads 0 before the DOM updates and the test
# fails spuriously. Rewritten to a WAITING assertion on the first match.
_ASSERT_COUNT_RE = re.compile(
    r"""^(?P<indent>[ \t]*)assert\s+(?P<loc>.+?)\.count\(\)\s*(?:>\s*0|>=\s*1)\s*$""",
    re.MULTILINE)
_COUNT_GT_RE = re.compile(
    r"""expect\(\s*(?P<loc>.+?)\s*\)\.to_have_count_greater_than\(\s*(?P<n>\d+)\s*\)""")
# Invented "at least N" variants of to_have_count, e.g.
#   expect(X).to_have_count(1, minimum=True)
#   expect(X).to_have_count(1, minimum=True, timeout=5000)
_COUNT_MIN_RE = re.compile(
    r"""expect\(\s*(?P<loc>.+?)\s*\)\.to_have_count\(\s*(?P<n>\d+)\s*,"""
    r"""[^)]*minimum\s*=\s*True[^)]*\)""")


def postprocess_playwright_code(code: str) -> str:
    """Deterministically fix common LLM API slips so the module runs.

    LLMs frequently invent Playwright methods or forget imports; these are cheap,
    safe rewrites that turn a guaranteed crash into a real assertion:
    * ``expect(X).to_have_count_greater_than(N)`` -> ``assert (X).count() > N``
      (no such Playwright assertion exists).
    * add ``import re`` when ``re.`` is used but not imported.
    """
    # Invented "greater than" / "at least" count assertions -> a WAITING check.
    # `expect(loc.first).to_be_visible()` auto-waits for the first match, so it
    # handles async-rendered results (e.g. search hits); a bare `loc.count()` does
    # NOT wait and returns 0 before the SPA renders.
    code = _COUNT_GT_RE.sub(r"expect((\g<loc>).first).to_be_visible()", code)
    code = _COUNT_MIN_RE.sub(r"expect((\g<loc>).first).to_be_visible()", code)
    code = _ASSERT_COUNT_RE.sub(
        r"\g<indent>expect((\g<loc>).first).to_be_visible()", code)
    # Missing `import re` (models use re.compile for name=... regex locators).
    if re.search(r"\bre\.", code) and not re.search(r"^\s*import re\b", code, re.MULTILINE):
        lines = code.splitlines()
        insert_at = 0
        for i, ln in enumerate(lines):
            if ln.startswith(("import ", "from ")):
                insert_at = i + 1
        lines.insert(insert_at, "import re")
        code = "\n".join(lines)
    return code


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
