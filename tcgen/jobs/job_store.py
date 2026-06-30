"""Persistent job state shared between the UI (reader) and worker (writer)."""

from __future__ import annotations

import datetime as _dt
import os
import tempfile
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from config.settings import RESULTS_DIR

JOBS_DIR = RESULTS_DIR / "jobs"
_MAX_LOG_LINES = 400  # kept inline for the UI; full log also goes to <id>.log

JobStatus = Literal["pending", "running", "done", "error", "cancelled"]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class JobState(BaseModel):
    id: str
    app_key: str
    pipelines: list[str]
    include_hybrid: bool = False
    evaluate: bool = True
    domain_context: str = ""
    user_story_ids: list[str] = Field(default_factory=list)
    repetitions: int = 1
    # Reuse the most recent Skript_C for this app instead of re-running the
    # (slow, deterministic) crawler.
    reuse_crawler: bool = False

    status: JobStatus = "pending"
    percent: float = 0.0
    message: str = ""
    logs: list[str] = Field(default_factory=list)
    result_id: str | None = None
    error: str | None = None
    pid: int | None = None

    created_at: str = Field(default_factory=_now)
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status in ("pending", "running")


class JobStore:
    def __init__(self, directory: Path | None = None):
        self.dir = directory or JOBS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.dir / f"{job_id}.json"

    def _log_path(self, job_id: str) -> Path:
        return self.dir / f"{job_id}.log"

    @staticmethod
    def new_id(app_key: str) -> str:
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{ts}_{app_key}_{uuid.uuid4().hex[:6]}"

    def save(self, job: JobState) -> None:
        """Atomically write the job JSON (write-temp + replace) to avoid torn reads."""
        path = self._path(job.id)
        fd, tmp = tempfile.mkstemp(dir=str(self.dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(job.model_dump_json(indent=2))
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def load(self, job_id: str) -> JobState:
        return JobState.model_validate_json(self._path(job_id).read_text(encoding="utf-8"))

    def append_log(self, job_id: str, line: str) -> None:
        with self._log_path(job_id).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def push_log(self, job: JobState, line: str) -> None:
        """Append to in-memory (capped) and on-disk full log."""
        stamped = f"{_dt.datetime.now().strftime('%H:%M:%S')}  {line}"
        job.logs.append(stamped)
        if len(job.logs) > _MAX_LOG_LINES:
            job.logs = job.logs[-_MAX_LOG_LINES:]
        self.append_log(job.id, stamped)

    def delete(self, job_id: str) -> None:
        """Remove a job's state, log, and process-log files."""
        for suffix in (".json", ".log", ".proc.log"):
            try:
                (self.dir / f"{job_id}{suffix}").unlink(missing_ok=True)
            except OSError:
                pass

    def list_ids(self) -> list[str]:
        return sorted((p.stem for p in self.dir.glob("*.json")), reverse=True)

    def list_jobs(self, limit: int = 30) -> list[JobState]:
        out: list[JobState] = []
        for jid in self.list_ids()[:limit]:
            try:
                out.append(self.load(jid))
            except Exception:  # noqa: BLE001
                continue
        return out
