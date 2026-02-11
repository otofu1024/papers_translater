from __future__ import annotations

import base64
import importlib
import mimetypes
from inspect import iscoroutine
from pathlib import Path
from typing import Any, Callable

import httpx


class OCRClientError(RuntimeError):
    """Raised when OCR parsing fails."""


class OCRClient:
    def __init__(
        self,
        base_url: str,
        timeout_sec: float = 30.0,
        parse_paths: list[str] | None = None,
        model: str | None = None,
        prompt: str | None = None,
        sdk_entrypoint: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.parse_paths = parse_paths or ["/ocr"]
        self.model = model
        self.prompt = prompt or (
            "Recognize the text in the image and output in Markdown format."
        )
        self.sdk_runner = self._load_sdk_runner(sdk_entrypoint)

    async def parse_image(self, image_path: Path) -> dict[str, Any]:
        if not image_path.exists():
            raise OCRClientError(f"Image not found: {image_path}")

        if self.sdk_runner is not None:
            return await self._parse_with_sdk(image_path)
        return await self._parse_with_http(image_path)

    async def _parse_with_sdk(self, image_path: Path) -> dict[str, Any]:
        assert self.sdk_runner is not None
        result = self.sdk_runner(image_path=image_path, base_url=self.base_url)
        if iscoroutine(result):
            result = await result
        if not isinstance(result, dict):
            raise OCRClientError("SDK OCR result must be a JSON object.")
        return result

    async def _parse_with_http(self, image_path: Path) -> dict[str, Any]:
        errors: list[str] = []
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            for path in self.parse_paths:
                url = f"{self.base_url}{path}"
                try:
                    response = await self._post_by_path(client, path, url, image_path)
                except httpx.HTTPError as exc:
                    errors.append(f"{url}: {exc.__class__.__name__}")
                    continue

                if response.status_code >= 400:
                    errors.append(f"{url}: status={response.status_code}")
                    continue

                try:
                    data = response.json()
                except ValueError as exc:
                    raise OCRClientError(f"OCR response is not valid JSON: {exc}") from exc

                if isinstance(data, dict):
                    return data
                raise OCRClientError("OCR response JSON must be an object.")

        joined = "; ".join(errors) if errors else "unknown error"
        raise OCRClientError(f"Failed to parse image via OCR server: {joined}")

    async def _post_by_path(
        self,
        client: httpx.AsyncClient,
        path: str,
        url: str,
        image_path: Path,
    ) -> httpx.Response:
        normalized = path.lower()
        if "chat/completions" in normalized:
            payload = self._build_chat_completions_payload(image_path)
            return await client.post(url, json=payload)

        mime = self._guess_mime_type(image_path)
        with image_path.open("rb") as f:
            return await client.post(
                url,
                files={"file": (image_path.name, f, mime)},
            )

    def _build_chat_completions_payload(self, image_path: Path) -> dict[str, Any]:
        data_url = self._to_data_url(image_path)
        payload: dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        }
        if self.model:
            payload["model"] = self.model
        return payload

    @staticmethod
    def _to_data_url(image_path: Path) -> str:
        image_bytes = image_path.read_bytes()
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        mime = OCRClient._guess_mime_type(image_path)
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _guess_mime_type(image_path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(image_path))
        if mime:
            return mime
        return "image/png"

    @staticmethod
    def _load_sdk_runner(entrypoint: str | None) -> Callable[..., Any] | None:
        if not entrypoint:
            return None

        if ":" not in entrypoint:
            raise OCRClientError("OCR_SDK_ENTRYPOINT must be in 'module:function' format.")
        module_name, func_name = entrypoint.split(":", maxsplit=1)
        module = importlib.import_module(module_name)
        runner = getattr(module, func_name, None)
        if runner is None or not callable(runner):
            raise OCRClientError(f"OCR SDK entrypoint not callable: {entrypoint}")
        return runner
