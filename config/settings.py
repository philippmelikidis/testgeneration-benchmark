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
    llm_provider: Literal["ollama", "openai"] = "ollama"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_judge_model: str = "qwen2.5:14b"

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_judge_model: str = "gpt-4o"

    # --- generation behaviour ---
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    agent_max_steps: int = 25
    agent_repair: bool = True            # one validate+repair round on Skript_L
    crawler_max_states: int = 40
    crawler_max_depth: int = 4
    crawler_max_actions_per_state: int = 12
    crawler_max_scenarios: int = 12

    # --- execution ---
    headless: bool = True
    flakiness_runs: int = 3
    # SPA settle: cap for the networkidle wait (Juice Shop polls in the
    # background and never truly idles, so keep this small) + a short paint pause.
    settle_timeout_ms: int = 1500
    settle_pause_ms: int = 400
    # Per-action timeout the generated test harness applies. High enough that
    # slow SPA renders/animations don't time out spuriously, but below the 30s
    # Playwright default so genuinely broken scripts still fail in reasonable time.
    test_action_timeout_ms: int = 15000

    @property
    def generation_model(self) -> str:
        return self.ollama_model if self.llm_provider == "ollama" else self.openai_model

    @property
    def judge_model(self) -> str:
        return (
            self.ollama_judge_model
            if self.llm_provider == "ollama"
            else self.openai_judge_model
        )


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
