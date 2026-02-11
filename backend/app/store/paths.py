from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings


@dataclass(frozen=True)
class JobPaths:
    output_root: Path
    jobs_root: Path
    job_dir: Path
    input_pdf: Path
    meta_json: Path
    job_log: Path
    pages_dir: Path
    ocr_dir: Path
    md_dir: Path
    result_md: Path


def build_job_paths(job_id: str, settings: Settings) -> JobPaths:
    output_root = settings.repo_root / settings.output_dir
    jobs_root = output_root / "jobs"
    job_dir = jobs_root / job_id
    pages_dir = job_dir / "pages"
    ocr_dir = job_dir / "ocr"
    md_dir = job_dir / "md"
    return JobPaths(
        output_root=output_root,
        jobs_root=jobs_root,
        job_dir=job_dir,
        input_pdf=job_dir / "input.pdf",
        meta_json=job_dir / "meta.json",
        job_log=job_dir / "job.log",
        pages_dir=pages_dir,
        ocr_dir=ocr_dir,
        md_dir=md_dir,
        result_md=md_dir / "result.md",
    )


def ensure_job_dirs(paths: JobPaths) -> None:
    paths.job_dir.mkdir(parents=True, exist_ok=True)
    paths.pages_dir.mkdir(parents=True, exist_ok=True)
    paths.ocr_dir.mkdir(parents=True, exist_ok=True)
    paths.md_dir.mkdir(parents=True, exist_ok=True)

