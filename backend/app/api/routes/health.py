from __future__ import annotations

from typing import Tuple

import httpx
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models.schemas import HealthResponse, ServiceHealth

router = APIRouter(tags=["health"])


async def _probe(url: str, timeout: float) -> Tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        if response.status_code < 400:
            return True, f"reachable ({response.status_code})"
        return False, f"unhealthy ({response.status_code})"
    except httpx.HTTPError as exc:
        return False, f"unreachable ({exc.__class__.__name__})"


@router.get("/health", response_model=HealthResponse)
async def health() -> JSONResponse:
    settings = get_settings()

    ocr_ok, ocr_detail = await _probe(f"{settings.ocr_base_url}/docs", settings.http_timeout_sec)
    ollama_ok, ollama_detail = await _probe(
        f"{settings.ollama_base_url}/api/tags",
        settings.http_timeout_sec,
    )

    payload = HealthResponse(
        status="ok" if ocr_ok and ollama_ok else "degraded",
        ocr=ServiceHealth(ok=ocr_ok, detail=ocr_detail),
        ollama=ServiceHealth(ok=ollama_ok, detail=ollama_detail),
    )

    status_code = status.HTTP_200_OK if payload.status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=payload.model_dump())

