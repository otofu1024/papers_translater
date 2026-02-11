from __future__ import annotations

from pathlib import Path

from app.models.schemas import Block, PageResult


def _render_block(block: Block) -> str:
    text = (block.translated_text or block.text).strip()
    if not text:
        return ""

    block_type = block.type.lower()
    if block_type in {"title", "heading", "header"}:
        return f"### {text}"
    if block_type in {"list_item", "bullet"}:
        return f"- {text}"
    return text


def page_to_markdown(page: PageResult) -> str:
    lines = [line for block in page.blocks if (line := _render_block(block))]
    body = "\n\n".join(lines).strip()
    if not body:
        return f"## Page {page.page}\n"
    return f"## Page {page.page}\n\n{body}\n"


def write_page_markdown(page: PageResult, output_path: Path) -> str:
    markdown = page_to_markdown(page)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return markdown


def merge_page_markdowns(page_markdowns: list[str]) -> str:
    chunks = [chunk.strip() for chunk in page_markdowns if chunk.strip()]
    return "\n\n".join(chunks).strip() + ("\n" if chunks else "")


def write_result_markdown(page_markdowns: list[str], output_path: Path) -> str:
    merged = merge_page_markdowns(page_markdowns)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8")
    return merged
