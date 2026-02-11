from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Path as FPath, UploadFile, status
from fastapi.responses import FileResponse, PlainTextResponse

from app.core.config import get_settings
from app.models.schemas import JobCreateResponse, JobMeta
from app.pipeline.run_job import run_job
from app.store.paths import JobPaths, build_job_paths, ensure_job_dirs
from app.store.state import init_meta, load_meta, save_meta

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _resolve_paths(job_id: str) -> JobPaths:
    return build_job_paths(job_id=job_id, settings=get_settings())


def _assert_pdf(upload: UploadFile) -> None:
    filename = upload.filename or ""
    content_type = upload.content_type or ""
    if filename.lower().endswith(".pdf"):
        return
    if content_type.lower() == "application/pdf":
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Only PDF files are supported.",
    )


def _load_meta_or_404(meta_path: Path) -> JobMeta:
    if not meta_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return load_meta(meta_path)


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> JobCreateResponse:
    _assert_pdf(file)

    job_id = uuid.uuid4().hex
    paths = _resolve_paths(job_id)
    ensure_job_dirs(paths)

    with paths.input_pdf.open("wb") as dst:
        shutil.copyfileobj(file.file, dst)

    filename = file.filename or "input.pdf"
    meta = init_meta(
        job_id=job_id,
        filename=filename,
        extra={"input_bytes": paths.input_pdf.stat().st_size},
    )
    save_meta(paths.meta_json, meta)
    background_tasks.add_task(run_job, job_id)
    await file.close()
    return JobCreateResponse(job_id=job_id)


@router.get("/{job_id}", response_model=JobMeta)
async def get_job(job_id: str) -> JobMeta:
    paths = _resolve_paths(job_id)
    return _load_meta_or_404(paths.meta_json)


@router.get("/{job_id}/result")
async def get_result(job_id: str) -> FileResponse:
    paths = _resolve_paths(job_id)
    _load_meta_or_404(paths.meta_json)
    if not paths.result_md.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not available yet.",
        )
    return FileResponse(
        path=paths.result_md,
        media_type="text/markdown; charset=utf-8",
        filename=f"{job_id}.md",
    )


@router.get("/{job_id}/pages/{page_no}")
async def get_page_markdown(
    job_id: str,
    page_no: int = FPath(..., ge=1),
) -> PlainTextResponse:
    paths = _resolve_paths(job_id)
    _load_meta_or_404(paths.meta_json)
    page_file = paths.md_dir / f"{page_no:03d}.md"
    if not page_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page markdown not found.")
    return PlainTextResponse(page_file.read_text(encoding="utf-8"))
