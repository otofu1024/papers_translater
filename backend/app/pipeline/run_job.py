from __future__ import annotations

import traceback
from datetime import UTC, datetime

from app.clients.ocr_client import OCRClient
from app.clients.ollama_client import OllamaClient
from app.core.config import Settings, get_settings
from app.models.schemas import JobMeta, JobStatus
from app.pipeline.ocr_page import run_ocr_for_page
from app.pipeline.order_blocks import order_page_blocks
from app.pipeline.render_pdf import render_pdf_to_images
from app.pipeline.to_markdown import write_page_markdown, write_result_markdown
from app.pipeline.translate import translate_page_blocks
from app.store.paths import JobPaths, build_job_paths
from app.store.state import load_meta, save_meta, update_meta


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _append_job_log(paths: JobPaths, message: str) -> None:
    line = f"{_utc_now_iso()} {message.rstrip()}\n"
    paths.job_log.parent.mkdir(parents=True, exist_ok=True)
    with paths.job_log.open("a", encoding="utf-8") as fp:
        fp.write(line)


def _save(paths: JobPaths, meta: JobMeta) -> JobMeta:
    save_meta(paths.meta_json, meta)
    return meta


def _progress_for_page(page_index: int, total_pages: int) -> float:
    if total_pages <= 0:
        return 0.2
    return min(0.95, 0.2 + (0.75 * page_index / total_pages))


async def run_job(job_id: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    paths = build_job_paths(job_id=job_id, settings=settings)
    meta = load_meta(paths.meta_json)
    _append_job_log(paths, f"Job started: {job_id}")

    try:
        meta = _save(
            paths,
            update_meta(
                meta,
                status=JobStatus.RUNNING,
                stage="rendering",
                progress=0.05,
                error=None,
            ),
        )
        _append_job_log(paths, "Rendering PDF pages")
        page_images = render_pdf_to_images(
            pdf_path=paths.input_pdf,
            output_dir=paths.pages_dir,
            dpi=settings.render_dpi,
        )
        if not page_images:
            raise RuntimeError("No pages were rendered from PDF.")
        _append_job_log(paths, f"Rendered pages: {len(page_images)}")

        ocr_client = OCRClient(
            base_url=settings.ocr_base_url,
            timeout_sec=settings.http_timeout_sec,
            parse_paths=settings.ocr_parse_path_list,
            sdk_entrypoint=settings.ocr_sdk_entrypoint,
        )
        ollama_client = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_sec=settings.ollama_timeout_sec,
        )

        page_markdowns: list[str] = []
        total = len(page_images)
        for idx, image_path in enumerate(page_images, start=1):
            _append_job_log(paths, f"Page {idx}/{total}: OCR")
            meta = _save(
                paths,
                update_meta(
                    meta,
                    stage=f"ocr:{idx}/{total}",
                    progress=_progress_for_page(idx - 1, total),
                ),
            )

            ocr_json_path = paths.ocr_dir / f"{idx:03d}.json"
            page_result = await run_ocr_for_page(
                image_path=image_path,
                page=idx,
                ocr_client=ocr_client,
                ocr_output_path=ocr_json_path,
            )
            page_result = order_page_blocks(page_result)

            _append_job_log(paths, f"Page {idx}/{total}: translation")
            page_result = await translate_page_blocks(
                page_result,
                client=ollama_client,
                max_chars=settings.translate_max_chars,
            )

            page_md_path = paths.md_dir / f"{idx:03d}.md"
            page_md = write_page_markdown(page_result, page_md_path)
            page_markdowns.append(page_md)

            meta = _save(
                paths,
                update_meta(
                    meta,
                    stage=f"done:{idx}/{total}",
                    progress=_progress_for_page(idx, total),
                ),
            )
            _append_job_log(paths, f"Page {idx}/{total}: done")

        write_result_markdown(page_markdowns=page_markdowns, output_path=paths.result_md)
        result_path = str(paths.result_md.relative_to(settings.repo_root))
        meta = _save(
            paths,
            update_meta(
                meta,
                status=JobStatus.SUCCEEDED,
                stage="completed",
                progress=1.0,
                result_path=result_path,
                error=None,
            ),
        )
        _append_job_log(paths, f"Job completed: {job_id}")
    except Exception as exc:  # noqa: BLE001
        _append_job_log(paths, f"Job failed: {exc}")
        _append_job_log(paths, traceback.format_exc())
        failed_meta = update_meta(
            meta,
            status=JobStatus.FAILED,
            stage="failed",
            error=str(exc),
        )
        save_meta(paths.meta_json, failed_meta)

