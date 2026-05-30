"""Launch and query background jobs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    ) -> str:
        """Persist a pending job and spawn a detached worker process."""
        job = JobState(
            id=self.store.new_id(app_key),
            app_key=app_key,
            pipelines=[p.value for p in pipelines],
            include_hybrid=include_hybrid,
            evaluate=evaluate,
            domain_context=domain_context,
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
