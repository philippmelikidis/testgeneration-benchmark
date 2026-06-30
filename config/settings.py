"""Typed runtime configuration.

All settings are read from environment variables (prefix ``TCGEN_``) and the
optional ``.env`` file. Target-application definitions live in YAML files under
``config/targets/`` and are loaded separately via :func:`load_target`.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGETS_DIR = PROJECT_ROOT / "config" / "targets"
GENERATED_DIR = PROJECT_ROOT / "generated"
RESULTS_DIR = PROJECT_ROOT / "results"


class Settings(BaseSettings):
    """Process-wide configuration.

    The defaults favour a fully local, no-cost setup (Ollama). Switching the
    provider to ``openai`` only requires setting the provider field and an API
    key; no code changes are needed.
    """

    model_config = SettingsConfigDict(
        env_prefix="TCGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- provider selection ---
    llm_provider: Literal["ollama", "openai", "gemini"] = "ollama"

    # --- Ollama (local or Ollama Cloud) ---
    # For Ollama Cloud: set base_url to https://ollama.com and provide an API key.
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_key: str = ""  # set for Ollama Cloud (Bearer auth)
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_judge_model: str = "qwen2.5:14b"
    # Keep reasoning OFF for thinking models so the code lands in `content`
    # instead of being buried in/truncated by the reasoning stream.
    ollama_think: bool = False

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_judge_model: str = "gpt-4o"

    # --- Gemini (google-genai) ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_judge_model: str = "gemini-2.5-flash"

    # --- generation behaviour ---
    llm_temperature: float = 0.1
    # Per-request timeout (s) for LLM calls. Without it a stalled cloud request
    # hangs the agent loop indefinitely (each exploration step is one call).
    llm_request_timeout_s: float = 120.0
    # Generous so thinking models (e.g. glm-5.1, gpt-oss) have room for the code
    # AFTER their reasoning tokens; too small truncates the script to nothing.
    llm_max_tokens: int = 8192
    agent_max_steps: int = 25
    agent_repair: bool = True            # one validate+repair round on Skript_L
    # --- agent browser backend ---
    # "playwright_mcp": explore via the official Microsoft Playwright MCP server
    # (@playwright/mcp, requires Node 18+/npx); "inprocess": the bundled
    # in-process Playwright harness. MCP is the default; it falls back to
    # in-process (recorded in script meta) if the server cannot be launched.
    agent_browser_backend: Literal["playwright_mcp", "inprocess"] = "playwright_mcp"
    playwright_mcp_command: str = "npx"
    playwright_mcp_args: str = "@playwright/mcp@latest --headless --isolated --browser chromium"
    playwright_mcp_start_timeout_s: float = 90.0
    crawler_max_states: int = 40
    crawler_max_depth: int = 4
    # Generous per-state interaction budget: the crawler is the COMPLETENESS
    # baseline, so prefer covering the reachable surface over speed.
    crawler_max_actions_per_state: int = 25
    crawler_max_scenarios: int = 12
    # Per-action timeout during exploration (ms). This bounds how long a click/
    # fill waits for an element to become actionable. On a local SPA real
    # elements respond in well under this; a longer value only wastes time
    # waiting on non-actionable (e.g. decorative cursor:pointer) elements, which
    # is what makes the crawl *look* hung. Completeness comes from the broadened
    # element harvest, not from waiting longer on dead elements.
    crawler_action_timeout_ms: int = 4000
    # Wall-clock cap (s) for the whole exploration; 0 = no cap (default). The
    # crawler is allowed to run as long as it needs for full coverage; set a
    # positive value only if you want to bound run time.
    crawler_time_budget_s: int = 0

    # --- execution ---
    headless: bool = True
    flakiness_runs: int = 3
    # How many times the non-deterministic LLM stages (Skript_L/H) and the judge
    # are repeated; results are aggregated to a mean with std + anomalies.
    repetitions: int = 1
    # SPA settle: cap for the networkidle wait (Juice Shop polls in the
    # background and never truly idles, so keep this small) + a short paint pause.
    settle_timeout_ms: int = 1500
    settle_pause_ms: int = 400
    # Per-action timeout the generated test harness applies. Below the 30s
    # Playwright default so broken/unstable tests fail fast (they otherwise burn
    # this much × retries × flakiness_runs). The harness also disables CSS
    # animations, so elements settle quickly and this can stay modest.
    test_action_timeout_ms: int = 8000

    @property
    def generation_model(self) -> str:
        return {
            "ollama": self.ollama_model,
            "openai": self.openai_model,
            "gemini": self.gemini_model,
        }[self.llm_provider]

    @property
    def judge_model(self) -> str:
        return {
            "ollama": self.ollama_judge_model,
            "openai": self.openai_judge_model,
            "gemini": self.gemini_judge_model,
        }[self.llm_provider]


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()


# --------------------------------------------------------------------------- #
# Target-application definitions
# --------------------------------------------------------------------------- #
class UserStory(BaseModel):
    """A single requirement the generated test should cover."""

    id: str
    title: str
    text: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class TargetApp(BaseModel):
    """A target web application under test."""

    key: str
    name: str
    base_url: str
    description: str = ""
    # Optional credentials for apps that require login (e.g. OpenCart admin).
    username: str | None = None
    password: str | None = None
    # Hints that help both pipelines stay on-task (not hard selectors).
    entry_paths: list[str] = Field(default_factory=lambda: ["/"])
    avoid_url_substrings: list[str] = Field(default_factory=list)
    # CSS selectors of blocking overlays (welcome dialog, cookie banner). The
    # test harness auto-dismisses these so they don't intercept actions. This is
    # environment setup applied identically to every pipeline, not result tuning.
    dismiss_selectors: list[str] = Field(default_factory=list)
    user_stories: list[UserStory] = Field(default_factory=list)


def load_target(key: str) -> TargetApp:
    """Load a target definition by key from ``config/targets/<key>.yaml``."""
    path = TARGETS_DIR / f"{key}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No target definition at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TargetApp.model_validate(data)


def list_targets() -> list[str]:
    """Return the keys of all available target definitions."""
    if not TARGETS_DIR.exists():
        return []
    return sorted(p.stem for p in TARGETS_DIR.glob("*.yaml"))
