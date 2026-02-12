from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.clients.ocr_client import OCRClient
from app.models.schemas import Block, PageResult

PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")
INLINE_SPACE_RE = re.compile(r"\s+")
FALLBACK_TOTAL_CHAR_LIMIT = 12000
FALLBACK_BLOCK_CHAR_LIMIT = 1800


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


def _extract_content_from_choices(raw: dict[str, Any]) -> str | None:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    return None


def _parse_array_blocks(raw_array: list[Any], page: int) -> list[Block]:
    if not raw_array:
        return []
    first = raw_array[0] if isinstance(raw_array[0], list) else raw_array
    if not isinstance(first, list):
        return []

    blocks: list[Block] = []
    for idx, item in enumerate(first, start=1):
        if not isinstance(item, dict):
            continue
        text = _extract_text(item)
        if not text:
            continue
        bbox = item.get("bbox_2d") or item.get("bbox") or item.get("box") or [0, 0, 0, 0]
        blocks.append(
            Block(
                id=str(item.get("id") or item.get("index") or f"p{page:03d}-b{idx:04d}"),
                type=str(item.get("type") or item.get("label") or "paragraph"),
                bbox=_as_bbox(bbox),
                text=text,
                page=page,
            )
        )
    return blocks


def _parse_text_to_blocks(text: str, page: int) -> list[Block]:
    stripped = text.strip()
    if not stripped:
        return []
    try:
        parsed = json.loads(stripped)
    except ValueError:
        parsed = None

    if isinstance(parsed, list):
        blocks = _parse_array_blocks(parsed, page=page)
        if blocks:
            return blocks
    if isinstance(parsed, dict):
        blocks = _extract_blocks(parsed)
        if blocks:
            normalized: list[Block] = []
            for idx, item in enumerate(blocks, start=1):
                txt = _extract_text(item)
                if not txt:
                    continue
                normalized.append(
                    Block(
                        id=str(item.get("id") or f"p{page:03d}-b{idx:04d}"),
                        type=str(item.get("type") or item.get("label") or "paragraph"),
                        bbox=_as_bbox(item.get("bbox") or item.get("box") or item.get("coordinates")),
                        text=txt,
                        page=page,
                    )
                )
            if normalized:
                return normalized

    return _fallback_text_blocks(stripped, page=page)


def _fallback_text_blocks(text: str, page: int) -> list[Block]:
    trimmed = text.strip()
    if not trimmed:
        return []

    if len(trimmed) > FALLBACK_TOTAL_CHAR_LIMIT:
        trimmed = trimmed[:FALLBACK_TOTAL_CHAR_LIMIT].rstrip()

    segments = _split_segments(trimmed)
    blocks: list[Block] = []
    for idx, segment in enumerate(segments, start=1):
        blocks.append(
            Block(
                id=f"p{page:03d}-b{idx:04d}",
                type="paragraph",
                bbox=[0.0, 0.0, 0.0, 0.0],
                text=segment,
                page=page,
            )
        )
    return blocks


def _split_segments(text: str) -> list[str]:
    raw_segments = [part.strip() for part in PARAGRAPH_SPLIT_RE.split(text) if part.strip()]
    if not raw_segments:
        raw_segments = [text.strip()]

    deduped: list[str] = []
    prev_key = ""
    for segment in raw_segments:
        key = _segment_key(segment)
        if key and key == prev_key:
            continue
        prev_key = key
        deduped.extend(_split_long_segment(segment, max_chars=FALLBACK_BLOCK_CHAR_LIMIT))

    return deduped or [text.strip()]


def _segment_key(text: str) -> str:
    return INLINE_SPACE_RE.sub(" ", text).strip().lower()


def _split_long_segment(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            split_at = text.rfind("\n", start, end)
            if split_at <= start:
                split_at = text.rfind(". ", start, end)
            if split_at <= start:
                split_at = end
        else:
            split_at = end

        chunk = text[start:split_at].strip()
        if chunk:
            parts.append(chunk)
        start = split_at
    return parts


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


def normalize_ocr_result(raw: Any, page: int) -> PageResult:
    blocks: list[Block] = []
    img_w = 0
    img_h = 0

    if isinstance(raw, dict):
        raw_blocks = _extract_blocks(raw)
        for idx, item in enumerate(raw_blocks, start=1):
            text = _extract_text(item)
            if not text:
                continue
            blocks.append(
                Block(
                    id=str(item.get("id") or f"p{page:03d}-b{idx:04d}"),
                    type=str(item.get("type") or item.get("label") or "paragraph"),
                    bbox=_as_bbox(item.get("bbox") or item.get("box") or item.get("coordinates")),
                    text=text,
                    page=page,
                )
            )
        img_w, img_h = _extract_image_size(raw)

        if not blocks:
            content = _extract_content_from_choices(raw)
            if content:
                blocks = _parse_text_to_blocks(content, page=page)

    if not blocks:
        blocks = _parse_array_blocks(raw if isinstance(raw, list) else [], page=page)

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
    page_result = normalize_ocr_result(raw, page=page)
    if page_result.img_w <= 0 or page_result.img_h <= 0:
        try:
            from PIL import Image

            with Image.open(image_path) as image:
                page_result = page_result.model_copy(
                    update={"img_w": image.width, "img_h": image.height}
                )
        except Exception:  # noqa: BLE001
            pass
    return page_result
