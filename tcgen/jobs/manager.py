"""Launch and query background jobs."""

from __future__ import annotations

import datetime as _dt
import os
import signal
import subprocess
import sys

from config.settings import PROJECT_ROOT
from tcgen.jobs.job_store import JobState, JobStore
from tcgen.orchestration.models import Pipeline


class JobManager:
    def __init__(self, store: JobStore | None = None):
        self.store = store or JobStore()

    def start(
        self,
        app_key: str,
        pipelines: list[Pipeline],
        *,
        include_hybrid: bool = False,
        evaluate: bool = True,
        domain_context: str = "",
        user_story_ids: list[str] | None = None,
        repetitions: int = 1,
        reuse_crawler: bool = False,
    ) -> str:
        """Persist a pending job and spawn a detached worker process."""
        job = JobState(
            id=self.store.new_id(app_key),
            app_key=app_key,
            pipelines=[p.value for p in pipelines],
            include_hybrid=include_hybrid,
            evaluate=evaluate,
            domain_context=domain_context,
            user_story_ids=user_story_ids or [],
            repetitions=repetitions,
            reuse_crawler=reuse_crawler,
        )
        self.store.save(job)

        proc_log = open(self.store.dir / f"{job.id}.proc.log", "w", encoding="utf-8")
        # start_new_session detaches the worker so it keeps running independently
        # of the Streamlit session / browser tab.
        subprocess.Popen(
            [sys.executable, "-m", "tcgen.jobs.worker", job.id],
            cwd=str(PROJECT_ROOT),
            stdout=proc_log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        return job.id

    def get(self, job_id: str) -> JobState:
        return self.store.load(job_id)

    def list(self, limit: int = 30) -> list[JobState]:
        return self.store.list_jobs(limit)

    def active(self) -> list[JobState]:
        return [j for j in self.store.list_jobs() if j.is_active]

    def cancel(self, job_id: str) -> JobState:
        """Terminate a running job's worker (and its child browser/pytest)."""
        job = self.store.load(job_id)
        if job.pid and job.is_active:
            try:
                # Worker was started in its own session, so kill the whole group.
                os.killpg(os.getpgid(job.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        job.status = "cancelled"
        job.message = "abgebrochen"
        job.finished_at = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        self.store.save(job)
        return job

    def delete(self, job_id: str) -> None:
        """Cancel if still running, then remove the job's files."""
        try:
            if self.store.load(job_id).is_active:
                self.cancel(job_id)
        except Exception:  # noqa: BLE001
            pass
        self.store.delete(job_id)

    def cleanup_finished(self) -> int:
        """Delete all non-active (done/error/cancelled) jobs. Returns count."""
        removed = 0
        for job in self.store.list_jobs(limit=1000):
            if not job.is_active:
                self.store.delete(job.id)
                removed += 1
        return removed
