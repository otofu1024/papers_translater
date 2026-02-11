from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import JobMeta, JobStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


def save_meta(meta_path: Path, meta: JobMeta) -> None:
    meta_path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def load_meta(meta_path: Path) -> JobMeta:
    raw = json.loads(meta_path.read_text(encoding="utf-8"))
    return JobMeta.model_validate(raw)


def init_meta(job_id: str, filename: str, extra: dict[str, object] | None = None) -> JobMeta:
    now = utc_now()
    return JobMeta(
        job_id=job_id,
        filename=filename,
        status=JobStatus.QUEUED,
        progress=0.0,
        stage="uploaded",
        created_at=now,
        updated_at=now,
        extra=extra or {},
    )


def update_meta(meta: JobMeta, **changes: object) -> JobMeta:
    payload = meta.model_dump()
    payload.update(changes)
    payload["updated_at"] = utc_now()
    return JobMeta.model_validate(payload)
