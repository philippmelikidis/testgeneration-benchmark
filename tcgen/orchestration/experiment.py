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
    mean_iso,
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
        self._provider = None  # lazy shared LLM provider for the runtime-repair loop

    def _get_provider(self):
        if self._provider is None:
            from tcgen.llm import get_provider
            self._provider = get_provider(self.settings)
        return self._provider

    def run(
        self,
        app_key: str,
        pipelines: list[Pipeline] | None = None,
        *,
        include_hybrid: bool = False,
        domain_context: str = "",
        user_story_ids: list[str] | None = None,
        repetitions: int | None = None,
        reuse_crawler: bool = False,
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
            evaluated=self.evaluate,
        )

        progress = Progress(self._total_units(pipelines, reps), sink)
        crawler_in = Pipeline.CRAWLER in pipelines

        # Crawler is deterministic -> generate once and reuse across runs.
        crawler_script: GeneratedScript | None = None
        if crawler_in:
            if reuse_crawler:
                crawler_script = self._load_last_crawler_script(app_key)
                if crawler_script is not None:
                    sink(None, "Crawler übersprungen — verwende letzten Skript_C "
                               "aus einem früheren Lauf wieder.")
                    if not crawler_script.meta.get("locator_catalog"):
                        sink(None, "⚠️  ACHTUNG: Dieser wiederverwendete Skript_C "
                                   "stammt aus einem Lauf VOR dem Locator-Katalog. "
                                   "Folgen: Skript_H-Grounding ist DEGRADIERT (kann "
                                   "auf externe Seiten wie GitHub abdriften) und die "
                                   "robusteren Crawler-Klicks fehlen. Für eine echte "
                                   "Bewertung den Crawler EINMAL neu laufen lassen "
                                   "(Reuse-Crawler AUS).")
                else:
                    sink(None, "Kein früherer Skript_C gefunden — Crawler wird neu "
                               "generiert.")
            if crawler_script is None:
                ph = progress.phase(1, "Skript_C: Generierung")
                try:
                    crawler_script = crawler_pipeline.generate(target, self.settings, phase=ph)
                except Exception as exc:  # noqa: BLE001
                    ph.log(f"FEHLER Crawler-Generierung: {exc}")
                    log.exception("Crawler generation failed")

        # Ground the judge's plausibility check in the app's REAL surface.
        self._app_context = self._build_app_context(crawler_script)

        # Collect samples: pipeline -> list of (script, execution, judge).
        # Each (pipeline, repetition) is an INDEPENDENT unit of work whose cost is
        # almost entirely waiting on the cloud LLM (generation) and the judge, so
        # we run several concurrently (``eval_workers``) instead of strictly
        # sequentially — this cuts wall-clock roughly linearly WITHOUT dropping any
        # repetition or detail. The crawler is deterministic (1 rep, reused).
        collected: dict[Pipeline, list[tuple]] = {p: [] for p in pipelines}
        gen_errors: dict[Pipeline, str] = {}

        tasks: list[tuple[Pipeline, int, int]] = []
        for pipeline in pipelines:
            pipe_reps = 1 if pipeline is Pipeline.CRAWLER else reps
            for i in range(pipe_reps):
                tasks.append((pipeline, i, pipe_reps))

        workers = max(1, min(int(getattr(self.settings, "eval_workers", 1)), len(tasks)))
        if workers == 1:
            for pl, i, pr in tasks:
                pl_, sample, err = self._run_rep(pl, i, pr, target, crawler_script,
                                                 domain_context, progress)
                if err:
                    gen_errors[pl_] = err
                if sample is not None:
                    collected[pl_].append(sample)
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            sink(None, f"Parallele Auswertung: {workers} gleichzeitige Läufe "
                       f"({len(tasks)} Einheiten)")
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = [pool.submit(self._run_rep, pl, i, pr, target, crawler_script,
                                    domain_context, progress)
                        for pl, i, pr in tasks]
                for fut in as_completed(futs):
                    pl_, sample, err = fut.result()
                    if err:
                        gen_errors[pl_] = err
                    if sample is not None:
                        collected[pl_].append(sample)

        denom, denom_source = self._coverage_denominator(crawler_script, crawler_in,
                                                         collected)
        for pipeline in pipelines:
            result = self._aggregate(collected[pipeline], denom, gen_errors.get(pipeline),
                                     pipeline, app_key)
            record.pipelines.append(result)

        from tcgen.util import same_model_family
        record.notes = (f"coverage_denominator={denom} ({denom_source}) "
                        f"repetitions={reps} "
                        f"judge_model={self.settings.judge_model} "
                        f"judge_in_family="
                        f"{same_model_family(self.settings.generation_model, self.settings.judge_model)} "
                        f"stories={[s.id for s in target.user_stories]}")
        path = self.store.save(record)
        progress.finish(f"gespeichert: {path.name}")
        return record

    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_app_context(crawler_script: GeneratedScript | None) -> str:
        """Compact 'this really exists' surface for the judge, from the crawler.

        Gives the LLM-as-judge the real routes + element labels the crawler
        discovered, so it can tell genuine app routes/elements (e.g. /#/search)
        from invented ones instead of guessing blind from the base URL alone."""
        if crawler_script is None:
            return ""
        meta = crawler_script.meta or {}
        routes = meta.get("routes") or []
        catalog = meta.get("locator_catalog") or []
        labels = sorted({(c.get("label") or "").strip()
                         for c in catalog if c.get("label")})
        parts: list[str] = []
        if routes:
            parts.append("Routes: " + ", ".join(routes[:40]))
        if labels:
            parts.append("UI elements/labels: " + ", ".join(labels[:80]))
        return "\n".join(parts)

    def _load_last_crawler_script(self, app_key: str) -> GeneratedScript | None:
        """Return the most recent non-empty Skript_C for this app, or None.

        Lets a run reuse an existing crawler artefact instead of re-running the
        slow (but deterministic) exploration. Records are newest-first."""
        try:
            records = self.store.list_records()
        except Exception:  # noqa: BLE001
            return None
        for rec in records:
            if rec.app_key != app_key:
                continue
            for pr in rec.pipelines:
                if pr.script.pipeline is Pipeline.CRAWLER and pr.script.code.strip():
                    return pr.script
        return None

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
            # Crawler: generated once and executed/judged once (deterministic).
            pipe_reps = 1 if p is Pipeline.CRAWLER else reps
            gen = 0 if p is Pipeline.CRAWLER else reps      # L/H regenerate per run
            units += gen + (2 * pipe_reps if self.evaluate else 0)  # exec + judge
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

    def _run_rep(self, pipeline, i, pipe_reps, target, crawler_script,
                 domain_context, progress):
        """One independent (pipeline, repetition) unit: generate -> execute ->
        judge. Returns ``(pipeline, sample_or_None, error_or_None)``. Safe to run
        concurrently: each rep gets its own provider (thread-safe) and an isolated
        execution work dir (``work_tag``), so nothing is shared/overwritten."""
        label = pipeline.script_label
        tag = f"(Lauf {i + 1}/{pipe_reps})"
        try:
            script = self._generate(pipeline, target, crawler_script,
                                    domain_context, progress, tag, reps_done=i)
        except Exception as exc:  # noqa: BLE001
            log.exception("Generation failed for %s", pipeline)
            return pipeline, None, f"generation failed: {exc}"
        ex = jd = None
        if self.evaluate:
            work_tag = f"{pipeline.value}_r{i}"
            ex = self._execute(script, pipeline, target, progress, label, tag, work_tag)
            jd = self._judge(script, pipeline, target, progress, label, tag)
        return pipeline, (script, ex, jd), None

    def _execute(self, script, pipeline, target, progress, label, tag, work_tag=""):
        ph = progress.phase(1, f"{label}: Ausführung {tag}")
        if not script.code.strip():
            ph.log("leeres Skript — Ausführung übersprungen")
            return ExecutionResult(first_error="leeres Skript (LLM lieferte keinen Code)")
        try:
            ex = self.runner.run(script, phase=ph, work_tag=work_tag)
        except Exception as exc:  # noqa: BLE001
            ph.log(f"FEHLER Ausführung {label}: {exc}")
            log.exception("Execution failed for %s", label)
            return ExecutionResult(first_error=str(exc))
        # Execute-verify-repair: only the non-deterministic LLM pipelines, and only
        # if they actually ran with failures. The crawler is deterministic and
        # exempt (keeps it the clean, untouched baseline). Fixes each red test
        # against its REAL Playwright error — the single biggest SSR lever.
        rounds = getattr(self.settings, "runtime_repair_rounds", 0)
        if (pipeline is not Pipeline.CRAWLER and rounds > 0
                and ex.executed and ex.n_failed > 0):
            try:
                from tcgen.pipelines.runtime_repair import runtime_repair
                script, ex = runtime_repair(
                    script, target, self.runner, self._get_provider(), self.settings,
                    initial_exec=ex, app_surface=getattr(self, "_app_context", ""),
                    max_rounds=rounds, work_tag=work_tag, phase=ph)
            except Exception as exc:  # noqa: BLE001
                ph.log(f"Laufzeit-Repair übersprungen ({exc})")
                log.exception("Runtime repair failed for %s", label)
        # Requirement-based completeness: how many user stories a PASSING test in
        # the FINAL (post-repair) suite actually verifies. Uniform across pipelines
        # (crawler/LLM alike); measured only if the target declares story
        # signatures, else ISO completeness falls back to surface coverage.
        try:
            from tcgen.runner.metrics import objective
            key_elements = [s.key_elements for s in target.user_stories]
            if any(key_elements):
                covered, total = objective.story_coverage(
                    script.code, set(ex.passed_functions), key_elements)
                ex.story_covered, ex.story_total = covered, total
                ph.log(f"Story-Abdeckung: {covered}/{total} verifiziert")
        except Exception as exc:  # noqa: BLE001
            log.warning("Story coverage computation failed for %s: %s", label, exc)
        return ex

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
                metrics=metrics, app_context=getattr(self, "_app_context", ""),
                phase=ph)
        except Exception as exc:  # noqa: BLE001
            ph.log(f"FEHLER Judge {label}: {exc}")
            log.exception("Judge failed for %s", label)
            return JudgeScores()

    def _coverage_denominator(self, crawler_script, crawler_in,
                              collected) -> tuple[int | None, str]:
        """Completeness denominator; returns ``(value, source)``.

        PRIMARY: distinct user-facing affordances (role, label) from the
        crawler's catalog — rep-independent and robust against nth-of-type
        DOM-node noise (see inline note). Secondary: the crawler's
        ``discovered_elements`` count. FALLBACK (no crawler in the run): the
        union of locators any pipeline exercised across all reps — that union
        grows with the repetition count, so union-denominator runs are not
        comparable to crawler-denominator runs; the source string is recorded
        in the experiment notes to keep that visible."""
        # Stable, FAIR denominator: the number of DISTINCT user-facing UI
        # affordances the crawler catalogued — i.e. distinct (role, label) pairs,
        # not raw DOM-node signatures. `discovered_elements` counted every distinct
        # DOM node (e.g. the items-per-page value "15" harvested as five different
        # nth-of-type nodes, every product tile, decorative generics), inflating the
        # denominator to ~95 and crushing completeness to ~0.08 for ALL pipelines,
        # including the crawler baseline itself. Collapsing to distinct affordances
        # (~25-30) measures "share of the app's real interactive surface covered",
        # is REP-INDEPENDENT (unlike the exercised-locator union, which balloons
        # over 50 reps), and is comparable across runs. The union is kept only as a
        # fallback when no crawler ran.
        if crawler_in and crawler_script is not None:
            catalog = crawler_script.meta.get("locator_catalog") or []
            affordances = {
                (c.get("role") or "", (c.get("label") or "").strip().lower())
                for c in catalog if (c.get("label") or "").strip()
            }
            if affordances:
                return len(affordances), "crawler_affordances"
            d = crawler_script.meta.get("discovered_elements")
            if d:
                return d, "crawler_discovered"
        union: set[str] = set()
        for samples in collected.values():
            for (_s, ex, _j) in samples:
                if ex is not None:
                    union |= set(ex.exercised_locators)
        return (len(union) or None), "union_fallback(rep-abhängig)"

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
        # ISO-Correctness silently degrades to SSR-only when the judge yields no
        # score — flag it so the changed metric composition is visible.
        if mjudge.correctness is None:
            anomalies.append("Judge lieferte keinen Correctness-Score — "
                             "ISO-Correctness basiert nur auf der SSR")
        return PipelineResult(
            script=samples[0][0],
            execution=mexec,
            judge=mjudge,
            # Headline ISO = mean of the per-rep ISO values (consistent with the
            # reported per-metric std; map_to_iso over MEAN inputs diverges via
            # the rounding of exercised_coverage and the min-cap nonlinearity).
            iso=mean_iso(reps_flat),
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
