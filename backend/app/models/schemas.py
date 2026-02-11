from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    ok: bool
    detail: str


class HealthResponse(BaseModel):
    status: str
    ocr: ServiceHealth
    ollama: ServiceHealth


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobCreateResponse(BaseModel):
    job_id: str


class JobMeta(BaseModel):
    job_id: str
    filename: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=1.0)
    stage: str
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Block(BaseModel):
    id: str
    type: str
    bbox: list[float] = Field(min_length=4, max_length=4)
    text: str
    translated_text: str | None = None
    page: int


class PageResult(BaseModel):
    page: int
    img_w: int
    img_h: int
    blocks: list[Block] = Field(default_factory=list)
    markdown: str = ""
