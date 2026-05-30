"""Job worker: ``python -m tcgen.jobs.worker <job_id>``.

Runs in its own process (clean main thread for Playwright sync API) and writes
progress + logs to the job file as it goes. Invoked by :class:`JobManager`.
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import sys
import traceback
from typing import Optional

from tcgen.jobs.job_store import JobState, JobStore
from tcgen.orchestration.experiment import ExperimentRunner
from tcgen.orchestration.models import Pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("tcgen.worker")


def run_job(job_id: str) -> int:
    store = JobStore()
    job = store.load(job_id)
    job.status = "running"
    job.started_at = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    job.pid = os.getpid()
    job.message = "Worker gestartet"
    store.push_log(job, "Worker gestartet")
    store.save(job)

    def sink(pct: Optional[float], message: str) -> None:
        if pct is not None:
            job.percent = round(pct, 4)
        job.message = message
        store.push_log(job, (f"[{pct * 100:5.1f}%] " if pct is not None else "        ") + message)
        store.save(job)

    try:
        runner = ExperimentRunner(evaluate=job.evaluate)
        record = runner.run(
            job.app_key,
            [Pipeline(p) for p in job.pipelines],
            include_hybrid=job.include_hybrid,
            domain_context=job.domain_context,
            sink=sink,
        )
        job.result_id = record.id
        job.status = "done"
        job.percent = 1.0
        job.message = f"fertig: {record.id}"
        store.push_log(job, f"Experiment fertig, gespeichert als {record.id}")
    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = str(exc)
        job.message = f"Fehler: {exc}"
        store.push_log(job, "FEHLER:\n" + traceback.format_exc())
        log.exception("Job %s failed", job_id)
    finally:
        job.finished_at = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        store.save(job)
    return 0 if job.status == "done" else 1


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m tcgen.jobs.worker <job_id>", file=sys.stderr)
        return 2
    return run_job(argv[0])


if __name__ == "__main__":
    raise SystemExit(main())
