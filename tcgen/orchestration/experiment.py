"""End-to-end experiment runner.

Generates scripts for the selected pipelines, executes them, scores them with
the DeepEval judge, maps the result onto ISO 25010, and persists one
:class:`ExperimentRecord`. Progress is reported through a weighted
:class:`~tcgen.progress.Progress` so the UI/job layer can show an overall
percentage plus live log lines. Each pipeline is isolated: a failure in one is
recorded as an error and does not abort the others.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from typing import Optional

from config.settings import Settings, TargetApp, get_settings, load_target
from tcgen.orchestration.models import (
    ExperimentRecord,
    GeneratedScript,
    JudgeScores,
    Pipeline,
    PipelineResult,
)
from tcgen.orchestration.results_store import ResultsStore
from tcgen.pipelines.crawler import serializer as crawler_pipeline
from tcgen.pipelines.hybrid import generate as hybrid_generate
from tcgen.pipelines.llm_agent import generate as agent_generate
from tcgen.pipelines.llm_agent.agent import _story_block
from tcgen.progress import Progress, Sink
from tcgen.runner import TestRunner
from tcgen.runner.metrics.deepeval_judge import DeepEvalJudge
from tcgen.runner.metrics.iso25010 import map_to_iso

log = logging.getLogger(__name__)

# Phase weights (generation dominates wall-clock time on LLM pipelines).
_W_GEN, _W_EXEC, _W_JUDGE = 3.0, 2.0, 1.0


def _log_sink(pct: Optional[float], message: str) -> None:
    prefix = f"[{pct * 100:5.1f}%] " if pct is not None else "         "
    log.info("%s%s", prefix, message)


class ExperimentRunner:
    def __init__(self, settings: Settings | None = None, *, evaluate: bool = True):
        self.settings = settings or get_settings()
        self.runner = TestRunner(self.settings)
        self.evaluate = evaluate
        self.store = ResultsStore()

    def run(
        self,
        app_key: str,
        pipelines: list[Pipeline] | None = None,
        *,
        include_hybrid: bool = False,
        domain_context: str = "",
        sink: Sink | None = None,
    ) -> ExperimentRecord:
        sink = sink or _log_sink
        target = load_target(app_key)
        pipelines = self._resolve_pipelines(pipelines, include_hybrid)

        record = ExperimentRecord(
            id=self._new_id(app_key),
            app_key=app_key,
            app_name=target.name,
            provider=self.settings.llm_provider,
            model=self.settings.generation_model,
        )
        scripts: dict[Pipeline, GeneratedScript] = {}
        progress = Progress(self._total_weight(pipelines), sink)

        for pipeline in pipelines:
            label = pipeline.script_label
            gen_phase = progress.phase(_W_GEN, f"{label}: Generierung")
            try:
                script = self._generate(pipeline, target, scripts, gen_phase, domain_context)
                scripts[pipeline] = script
            except Exception as exc:  # noqa: BLE001
                log.exception("Generation failed for %s", pipeline)
                gen_phase.log(f"FEHLER bei Generierung {label}: {exc}")
                record.pipelines.append(PipelineResult(
                    script=GeneratedScript(pipeline=pipeline, app_key=app_key, code=""),
                    error=f"generation failed: {exc}",
                ))
                continue

            result = PipelineResult(script=script)
            if self.evaluate:
                self._evaluate_into(result, target, progress)
            record.pipelines.append(result)

        path = self.store.save(record)
        progress.finish(f"gespeichert: {path.name}")
        return record

    # ------------------------------------------------------------------ #
    def _resolve_pipelines(self, pipelines, include_hybrid) -> list[Pipeline]:
        pipelines = list(pipelines or [Pipeline.CRAWLER, Pipeline.LLM_AGENT])
        if include_hybrid and Pipeline.HYBRID not in pipelines:
            pipelines.append(Pipeline.HYBRID)
        if Pipeline.HYBRID in pipelines and Pipeline.CRAWLER not in pipelines:
            pipelines.insert(0, Pipeline.CRAWLER)
        return pipelines

    def _total_weight(self, pipelines: list[Pipeline]) -> float:
        per = _W_GEN + (_W_EXEC + _W_JUDGE if self.evaluate else 0.0)
        return per * len(pipelines)

    def _generate(self, pipeline: Pipeline, target: TargetApp,
                  scripts: dict[Pipeline, GeneratedScript], phase,
                  domain_context: str) -> GeneratedScript:
        if pipeline is Pipeline.CRAWLER:
            return crawler_pipeline.generate(target, self.settings, phase=phase)
        if pipeline is Pipeline.LLM_AGENT:
            return agent_generate(target, self.settings, phase=phase)
        if pipeline is Pipeline.HYBRID:
            base = scripts.get(Pipeline.CRAWLER)
            if base is None:
                raise RuntimeError("Hybrid pipeline requires a crawler script first.")
            return hybrid_generate(base, target, self.settings,
                                   domain_context=domain_context, phase=phase)
        raise ValueError(f"Unknown pipeline {pipeline!r}")

    def _evaluate_into(self, result: PipelineResult, target: TargetApp,
                       progress: Progress) -> None:
        label = result.script.pipeline.script_label
        exec_phase = progress.phase(_W_EXEC, f"{label}: Ausführung")
        try:
            result.execution = self.runner.run(result.script, phase=exec_phase)
        except Exception as exc:  # noqa: BLE001
            result.error = f"execution failed: {exc}"
            exec_phase.log(f"FEHLER Ausführung {label}: {exc}")
            log.exception("Execution failed for %s", label)

        judge_phase = progress.phase(_W_JUDGE, f"{label}: Bewertung")
        try:
            judge = DeepEvalJudge(self.settings)
            result.judge = judge.judge(
                result.script.code, _story_block(target.user_stories),
                target.base_url, phase=judge_phase)
        except Exception as exc:  # noqa: BLE001
            result.judge = JudgeScores()
            result.error = (result.error or "") + f" | judge failed: {exc}"
            judge_phase.log(f"FEHLER Judge {label}: {exc}")
            log.exception("Judge failed for %s", label)

        result.iso = map_to_iso(result.execution, result.judge)

    @staticmethod
    def _new_id(app_key: str) -> str:
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{ts}_{app_key}_{uuid.uuid4().hex[:6]}"


def run_experiment(app_key: str, **kw) -> ExperimentRecord:
    """Module-level convenience wrapper."""
    settings = kw.pop("settings", None)
    evaluate = kw.pop("evaluate", True)
    return ExperimentRunner(settings, evaluate=evaluate).run(app_key, **kw)
