"""Persist experiment records as JSON files under ``results/``."""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import RESULTS_DIR
from tcgen.orchestration.models import ExperimentRecord


class ResultsStore:
    def __init__(self, directory: Path | None = None):
        self.dir = directory or RESULTS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: ExperimentRecord) -> Path:
        path = self.dir / f"{record.id}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load(self, record_id: str) -> ExperimentRecord:
        path = self.dir / f"{record_id}.json"
        return ExperimentRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_ids(self) -> list[str]:
        """Record ids, newest first (ids are timestamp-prefixed)."""
        return sorted((p.stem for p in self.dir.glob("*.json")), reverse=True)

    def list_records(self) -> list[ExperimentRecord]:
        records = []
        for rid in self.list_ids():
            try:
                records.append(self.load(rid))
            except Exception:  # noqa: BLE001 - skip corrupt files
                continue
        return records

    def latest(self) -> ExperimentRecord | None:
        ids = self.list_ids()
        return self.load(ids[0]) if ids else None
