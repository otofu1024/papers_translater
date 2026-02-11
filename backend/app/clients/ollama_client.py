from __future__ import annotations

from typing import Any

import httpx


class OllamaClientError(RuntimeError):
    """Raised when the Ollama API request fails."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_sec: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise OllamaClientError(f"Ollama request failed: {exc.__class__.__name__}") from exc

        if response.status_code >= 400:
            raise OllamaClientError(f"Ollama returned status {response.status_code}: {response.text[:400]}")

        try:
            body = response.json()
        except ValueError as exc:
            raise OllamaClientError(f"Ollama response is not JSON: {exc}") from exc

        text = self._extract_text(body)
        if not text:
            raise OllamaClientError("Ollama response did not contain translation text.")
        return text

    @staticmethod
    def _extract_text(body: dict[str, Any]) -> str:
        for key in ("response", "text", "output"):
            value = body.get(key)
            if isinstance(value, str):
                return value.strip()
        return ""

