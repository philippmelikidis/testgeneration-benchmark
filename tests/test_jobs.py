from tcgen.jobs.job_store import JobState, JobStore


def _job():
    return JobState(id="20260529-000000_juiceshop_abc123", app_key="juiceshop",
                    pipelines=["crawler", "llm_agent"])


def test_job_store_roundtrip(tmp_path):
    store = JobStore(directory=tmp_path)
    job = _job()
    store.save(job)
    assert store.list_ids() == [job.id]
    loaded = store.load(job.id)
    assert loaded.app_key == "juiceshop"
    assert loaded.is_active  # pending


def test_push_log_caps_inline_and_writes_file(tmp_path):
    store = JobStore(directory=tmp_path)
    job = _job()
    store.save(job)
    for i in range(500):
        store.push_log(job, f"line {i}")
    assert len(job.logs) == 400          # capped for the UI
    log_file = tmp_path / f"{job.id}.log"
    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8").count("\n") == 500  # full history on disk


def test_status_transitions(tmp_path):
    store = JobStore(directory=tmp_path)
    job = _job()
    job.status = "done"
    assert not job.is_active
    store.save(job)
    assert store.load(job.id).status == "done"
