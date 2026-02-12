from __future__ import annotations

import re
from collections.abc import Awaitable, Callable

from app.clients.ollama_client import OllamaClient
from app.models.schemas import Block, PageResult

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。．.!?])\s+")


def build_translation_prompt(source_text: str) -> str:
    return (
        "Task: Translate the following text into natural Japanese.\n"
        "Rules:\n"
        "- Keep numbers, units, URLs, references (e.g., Fig. 1) unchanged where possible.\n"
        "- Output translation only. Do not add explanations.\n"
        "- Avoid unnecessary newlines.\n\n"
        f"Text:\n{source_text}"
    )


def _split_long_text(text: str, max_chars: int) -> list[str]:
    trimmed = text.strip()
    if len(trimmed) <= max_chars:
        return [trimmed]

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(trimmed) if s.strip()]
    if len(sentences) <= 1:
        return [trimmed[i : i + max_chars] for i in range(0, len(trimmed), max_chars)]

    chunks: list[str] = []
    buf = ""
    for sentence in sentences:
        candidate = sentence if not buf else f"{buf} {sentence}"
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(sentence) <= max_chars:
            buf = sentence
        else:
            chunks.extend(sentence[i : i + max_chars] for i in range(0, len(sentence), max_chars))
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _clean_translation(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned.strip("`").strip()
    return cleaned


async def translate_text(text: str, client: OllamaClient, max_chars: int) -> str:
    source = text.strip()
    if not source:
        return ""

    chunks = _split_long_text(source, max_chars=max_chars)
    translated: list[str] = []
    for chunk in chunks:
        prompt = build_translation_prompt(chunk)
        out = await client.generate(prompt)
        translated.append(_clean_translation(out))
    return "\n".join(part for part in translated if part).strip()


async def translate_block(block: Block, client: OllamaClient, max_chars: int) -> Block:
    translated = await translate_text(block.text, client=client, max_chars=max_chars)
    return block.model_copy(update={"translated_text": translated})


async def translate_page_blocks(
    page: PageResult,
    client: OllamaClient,
    max_chars: int,
    on_block_done: Callable[[int, int], Awaitable[None] | None] | None = None,
) -> PageResult:
    translated_blocks: list[Block] = []
    total = len(page.blocks)
    for idx, block in enumerate(page.blocks, start=1):
        translated_blocks.append(await translate_block(block, client=client, max_chars=max_chars))
        if on_block_done is not None:
            callback_result = on_block_done(idx, total)
            if callback_result is not None:
                await callback_result
    return page.model_copy(update={"blocks": translated_blocks})
