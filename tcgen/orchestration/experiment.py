"""End-to-end experiment runner.

For each selected pipeline it generates a script, executes it, scores it with the
DeepEval judge, and maps the result onto ISO 25010. To account for LLM
non-determinism, the LLM stages (Skript_L, Skript_H) and the judge are repeated
``repetitions`` times and aggregated into a single result: the mean is the
headline, with per-metric standard deviation and anomalies reported separately.
The crawler is deterministic and is generated once, then re-evaluated per run.

A user-story filter scopes which stories drive the hybrid refiner and the
story-aware judge; Methode 1 (crawler, LLM agent) stays requirement-free.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from typing import Optional

from config.settings import Settings, TargetApp, get_settings, load_target
from tcgen.orchestration.aggregate import (
    aggregate_stats,
    flatten_result,
    mean_execution,
    mean_judge,
)
from tcgen.orchestration.models import (
    ExecutionResult,
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


def _log_sink(pct: Optional[float], message: str) -> None:
    prefix = f"[{pct * 100:5.1f}%] " if pct is not None else "         "
    log.info("%s%s", prefix, message)


def _check_reachable(url: str, timeout: float = 4.0) -> str | None:
    """Return None if the target responds, else a short reason string."""
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen(url, timeout=timeout)  # noqa: S310 - local target
        return None
    except urllib.error.HTTPError:
        return None  # server responded (even 4xx/5xx) -> it is up
    except Exception as exc:  # noqa: BLE001
        return str(exc)


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
        user_story_ids: list[str] | None = None,
        repetitions: int | None = None,
        sink: Sink | None = None,
    ) -> ExperimentRecord:
        sink = sink or _log_sink
        target = load_target(app_key)
        target = self._filter_stories(target, user_story_ids)

        unreachable = _check_reachable(target.base_url)
        if unreachable:
            msg = (f"Ziel-App {target.base_url} nicht erreichbar — läuft der "
                   f"Container/Server? ({unreachable})")
            sink(None, msg)
            raise RuntimeError(msg)

        pipelines = self._resolve_pipelines(pipelines, include_hybrid)
        reps = max(1, repetitions if repetitions is not None else self.settings.repetitions)
        record = ExperimentRecord(
            id=self._new_id(app_key),
            app_key=app_key,
            app_name=target.name,
            provider=self.settings.llm_provider,
            model=self.settings.generation_model,
        )

        progress = Progress(self._total_units(pipelines, reps), sink)
        crawler_in = Pipeline.CRAWLER in pipelines

        # Crawler is deterministic -> generate once and reuse across runs.
        crawler_script: GeneratedScript | None = None
        if crawler_in:
            ph = progress.phase(1, "Skript_C: Generierung")
            try:
                crawler_script = crawler_pipeline.generate(target, self.settings, phase=ph)
            except Exception as exc:  # noqa: BLE001
                ph.log(f"FEHLER Crawler-Generierung: {exc}")
                log.exception("Crawler generation failed")

        # Collect samples: pipeline -> list of (script, execution, judge)
        collected: dict[Pipeline, list[tuple]] = {}
        gen_errors: dict[Pipeline, str] = {}
        for pipeline in pipelines:
            label = pipeline.script_label
            samples: list[tuple] = []
            for i in range(reps):
                tag = f"(Lauf {i + 1}/{reps})"
                try:
                    script = self._generate(pipeline, target, crawler_script,
                                            domain_context, progress, tag, reps_done=i)
                except Exception as exc:  # noqa: BLE001
                    gen_errors[pipeline] = f"generation failed: {exc}"
                    log.exception("Generation failed for %s", pipeline)
                    continue
                ex = jd = None
                if self.evaluate:
                    ex = self._execute(script, progress, label, tag)
                    jd = self._judge(script, pipeline, target, progress, label, tag)
                samples.append((script, ex, jd))
            collected[pipeline] = samples

        denom = self._coverage_denominator(crawler_script, crawler_in, collected)
        for pipeline in pipelines:
            result = self._aggregate(collected[pipeline], denom, gen_errors.get(pipeline),
                                     pipeline, app_key)
            record.pipelines.append(result)

        record.notes = (f"coverage_denominator={denom} repetitions={reps} "
                        f"stories={[s.id for s in target.user_stories]}")
        path = self.store.save(record)
        progress.finish(f"gespeichert: {path.name}")
        return record

    # ------------------------------------------------------------------ #
    @staticmethod
    def _filter_stories(target: TargetApp, ids: list[str] | None) -> TargetApp:
        if not ids:
            return target
        kept = [s for s in target.user_stories if s.id in ids]
        return target.model_copy(update={"user_stories": kept})

    def _resolve_pipelines(self, pipelines, include_hybrid) -> list[Pipeline]:
        pipelines = list(pipelines or [Pipeline.CRAWLER, Pipeline.LLM_AGENT])
        if include_hybrid and Pipeline.HYBRID not in pipelines:
            pipelines.append(Pipeline.HYBRID)
        if Pipeline.HYBRID in pipelines and Pipeline.CRAWLER not in pipelines:
            pipelines.insert(0, Pipeline.CRAWLER)
        return pipelines

    def _total_units(self, pipelines: list[Pipeline], reps: int) -> float:
        units = 1 if Pipeline.CRAWLER in pipelines else 0  # crawler gen once
        for p in pipelines:
            gen = 0 if p is Pipeline.CRAWLER else reps      # L/H regenerate per run
            units += gen + (2 * reps if self.evaluate else 0)  # exec + judge per run
        return max(units, 1)

    def _generate(self, pipeline, target, crawler_script, domain_context,
                  progress, tag, reps_done) -> GeneratedScript:
        if pipeline is Pipeline.CRAWLER:
            if crawler_script is None:
                raise RuntimeError("crawler generation failed earlier")
            return crawler_script  # reuse deterministic artefact
        ph = progress.phase(1, f"{pipeline.script_label}: Generierung {tag}")
        if pipeline is Pipeline.LLM_AGENT:
            return agent_generate(target, self.settings, phase=ph)
        if pipeline is Pipeline.LLM_AGENT_STORY:
            return agent_generate(target, self.settings, phase=ph, with_stories=True)
        if pipeline is Pipeline.HYBRID:
            if crawler_script is None:
                raise RuntimeError("Hybrid requires a crawler script.")
            return hybrid_generate(crawler_script, target, self.settings,
                                   domain_context=domain_context, phase=ph)
        raise ValueError(f"Unknown pipeline {pipeline!r}")

    def _execute(self, script, progress, label, tag):
        ph = progress.phase(1, f"{label}: Ausführung {tag}")
        if not script.code.strip():
            ph.log("leeres Skript — Ausführung übersprungen")
            return ExecutionResult(first_error="leeres Skript (LLM lieferte keinen Code)")
        try:
            return self.runner.run(script, phase=ph)
        except Exception as exc:  # noqa: BLE001
            ph.log(f"FEHLER Ausführung {label}: {exc}")
            log.exception("Execution failed for %s", label)
            return ExecutionResult(first_error=str(exc))

    def _judge(self, script, pipeline, target, progress, label, tag):
        ph = progress.phase(1, f"{label}: Bewertung {tag}")
        if not script.code.strip():
            ph.log("leeres Skript — Bewertung übersprungen")
            return JudgeScores()
        try:
            # Story-aware judging for pipelines that RECEIVED the stories
            # (Skript_S, Skript_H); intrinsic for the story-free ones (C, L).
            story_aware = pipeline in (Pipeline.HYBRID, Pipeline.LLM_AGENT_STORY)
            story_block = _story_block(target.user_stories) if story_aware else None
            # Hallucination is not applicable to the deterministic crawler (it can
            # only emit elements it actually found) -> n/a, not 0.
            metrics = {"correctness", "appropriateness", "hallucination", "readability"}
            if pipeline is Pipeline.CRAWLER:
                metrics.discard("hallucination")
            return DeepEvalJudge(self.settings).judge(
                script.code, target.base_url, story_block=story_block,
                metrics=metrics, phase=ph)
        except Exception as exc:  # noqa: BLE001
            ph.log(f"FEHLER Judge {label}: {exc}")
            log.exception("Judge failed for %s", label)
            return JudgeScores()

    def _coverage_denominator(self, crawler_script, crawler_in, collected) -> int | None:
        if crawler_in and crawler_script is not None:
            d = crawler_script.meta.get("discovered_elements")
            if d:
                return d
        exercised = [
            ex.exercised_coverage
            for samples in collected.values()
            for (_s, ex, _j) in samples if ex is not None
        ]
        m = max(exercised, default=0)
        return m or None

    def _aggregate(self, samples, denom, gen_error, pipeline, app_key) -> PipelineResult:
        if not samples:
            return PipelineResult(
                script=GeneratedScript(pipeline=pipeline, app_key=app_key, code=""),
                error=gen_error or "no samples produced",
            )
        if all(not s[0].code.strip() for s in samples):
            gen_error = gen_error or "LLM lieferte leeren Code (Token-Limit/Thinking?)"
        if not self.evaluate:
            sc, _, _ = samples[0]
            return PipelineResult(script=sc, n_runs=len(samples))

        reps_flat = []
        for sc, ex, jd in samples:
            iso = map_to_iso(ex, jd, denom)
            reps_flat.append(flatten_result(
                PipelineResult(script=sc, execution=ex, judge=jd, iso=iso)))
        std, anomalies = aggregate_stats(reps_flat)
        mexec = mean_execution([ex for _s, ex, _j in samples])
        mjudge = mean_judge([jd for _s, _e, jd in samples])
        return PipelineResult(
            script=samples[0][0],
            execution=mexec,
            judge=mjudge,
            iso=map_to_iso(mexec, mjudge, denom),
            error=gen_error,
            n_runs=len(samples),
            metric_std=std,
            anomalies=anomalies,
            samples=reps_flat,
        )

    @staticmethod
    def _new_id(app_key: str) -> str:
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{ts}_{app_key}_{uuid.uuid4().hex[:6]}"


def run_experiment(app_key: str, **kw) -> ExperimentRecord:
    """Module-level convenience wrapper."""
    settings = kw.pop("settings", None)
    evaluate = kw.pop("evaluate", True)
    return ExperimentRunner(settings, evaluate=evaluate).run(app_key, **kw)
