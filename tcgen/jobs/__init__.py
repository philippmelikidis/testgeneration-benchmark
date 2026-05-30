"""Background job execution that survives Streamlit reruns and tab switches.

A job is launched as a detached subprocess (``python -m tcgen.jobs.worker``)
that runs the experiment and writes progress/logs to a JSON file. The UI only
polls that file, so navigating away or switching browser tabs never interrupts
the run.
"""

from tcgen.jobs.job_store import JobState, JobStore
from tcgen.jobs.manager import JobManager

__all__ = ["JobState", "JobStore", "JobManager"]
