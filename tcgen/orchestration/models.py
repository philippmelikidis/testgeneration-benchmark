"""Shared data models passed between pipelines, the runner, and the UI.

These are deliberately framework-agnostic Pydantic models so they serialise
cleanly to JSON for the results store and render directly in Streamlit.
"""

from __future__ import annotations

import datetime as _dt
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class Pipeline(str, Enum):
    """The three generation strategies of the study."""

    CRAWLER = "crawler"        # Skript_C  (Methode 1, traditional)
    LLM_AGENT = "llm_agent"    # Skript_L  (Methode 1, LLM-only)
    HYBRID = "hybrid"          # Skript_H  (Methode 2, LLM refines Skript_C)

    @property
    def script_label(self) -> str:
        return {"crawler": "Skript_C", "llm_agent": "Skript_L", "hybrid": "Skript_H"}[
            self.value
        ]


class GeneratedScript(BaseModel):
    """A test script produced by one pipeline for one (app, user-story?) target."""

    pipeline: Pipeline
    app_key: str
    language: str = "python"
    code: str
    path: str | None = None
    # Provenance / cost
    generation_time_s: float = 0.0
    model: str = ""
    provider: str = ""
    # Free-form pipeline-specific notes (states visited, agent steps, etc.)
    meta: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=_now)


class ExecutionResult(BaseModel):
    """Outcome of running a generated script through the pytest runner."""

    executed: bool = False           # did it run at all (import/collect ok)?
    passed: bool = False             # did all assertions pass?
    n_tests: int = 0
    n_passed: int = 0
    n_failed: int = 0
    duration_s: float = 0.0
    # Successful-Steps-Ratio: fraction of test steps that executed without error.
    ssr: float = 0.0
    # Distinct DOM elements interacted with (proxy for element coverage).
    element_coverage: int = 0
    # Flakiness: 0.0 = perfectly stable across repeated runs, 1.0 = fully unstable.
    flakiness: float = 0.0
    stdout: str = ""
    stderr: str = ""


class JudgeScores(BaseModel):
    """Semantic LLM-as-judge scores (DeepEval G-Eval), each in [0, 1]."""

    correctness: float | None = None
    appropriateness: float | None = None
    hallucination: float | None = None   # higher = more hallucination (worse)
    readability: float | None = None
    reasons: dict[str, str] = Field(default_factory=dict)


class Iso25010(BaseModel):
    """Functional-Suitability sub-characteristics per ISO/IEC 25010, in [0, 1]."""

    functional_correctness: float | None = None
    functional_completeness: float | None = None
    functional_appropriateness: float | None = None

    @property
    def overall(self) -> float | None:
        vals = [
            v
            for v in (
                self.functional_correctness,
                self.functional_completeness,
                self.functional_appropriateness,
            )
            if v is not None
        ]
        return round(sum(vals) / len(vals), 4) if vals else None


class PipelineResult(BaseModel):
    """Everything known about one pipeline's output for one app: the artefact,
    its execution behaviour, semantic judgement, and ISO mapping."""

    script: GeneratedScript
    execution: ExecutionResult = Field(default_factory=ExecutionResult)
    judge: JudgeScores = Field(default_factory=JudgeScores)
    iso: Iso25010 = Field(default_factory=Iso25010)
    error: str | None = None


class ExperimentRecord(BaseModel):
    """A full experiment run: one app, one or more pipelines, fully evaluated."""

    id: str
    app_key: str
    app_name: str
    provider: str
    model: str
    pipelines: list[PipelineResult] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now)
    notes: str = ""

    def by_pipeline(self, pipeline: Pipeline) -> PipelineResult | None:
        for r in self.pipelines:
            if r.script.pipeline == pipeline:
                return r
        return None
