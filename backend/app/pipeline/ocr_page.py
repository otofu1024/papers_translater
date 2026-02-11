from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.clients.ocr_client import OCRClient
from app.models.schemas import Block, PageResult


def _as_bbox(value: Any) -> list[float]:
    if isinstance(value, dict):
        keys = ("x1", "y1", "x2", "y2")
        if all(k in value for k in keys):
            return [float(value[k]) for k in keys]
        return [0.0, 0.0, 0.0, 0.0]

    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            return [float(v) for v in value]
        except (TypeError, ValueError):
            return [0.0, 0.0, 0.0, 0.0]
    return [0.0, 0.0, 0.0, 0.0]


def _extract_text(item: dict[str, Any]) -> str:
    for key in ("text", "content", "ocr_text", "value"):
        value = item.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def _extract_blocks(raw: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = (
        raw.get("blocks"),
        raw.get("elements"),
        raw.get("results"),
        raw.get("data", {}).get("blocks") if isinstance(raw.get("data"), dict) else None,
    )
    for value in candidates:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _extract_image_size(raw: dict[str, Any]) -> tuple[int, int]:
    width_keys = ("img_w", "width", "image_width", "w")
    height_keys = ("img_h", "height", "image_height", "h")

    width = 0
    height = 0
    for key in width_keys:
        if key in raw:
            try:
                width = int(raw[key])
            except (TypeError, ValueError):
                width = 0
            break
    for key in height_keys:
        if key in raw:
            try:
                height = int(raw[key])
            except (TypeError, ValueError):
                height = 0
            break
    return width, height


def normalize_ocr_result(raw: dict[str, Any], page: int) -> PageResult:
    raw_blocks = _extract_blocks(raw)
    blocks: list[Block] = []

    for idx, item in enumerate(raw_blocks, start=1):
        text = _extract_text(item)
        if not text:
            continue
        block = Block(
            id=str(item.get("id") or f"p{page:03d}-b{idx:04d}"),
            type=str(item.get("type") or item.get("label") or "paragraph"),
            bbox=_as_bbox(item.get("bbox") or item.get("box") or item.get("coordinates")),
            text=text,
            page=page,
        )
        blocks.append(block)

    img_w, img_h = _extract_image_size(raw)
    return PageResult(page=page, img_w=img_w, img_h=img_h, blocks=blocks)


async def run_ocr_for_page(
    image_path: Path,
    page: int,
    ocr_client: OCRClient,
    ocr_output_path: Path | None = None,
) -> PageResult:
    raw = await ocr_client.parse_image(image_path)
    if ocr_output_path is not None:
        ocr_output_path.parent.mkdir(parents=True, exist_ok=True)
        ocr_output_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return normalize_ocr_result(raw, page=page)

