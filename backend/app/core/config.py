from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    ocr_base_url: str = "http://127.0.0.1:8080"
    ocr_parse_paths: str = "/ocr,/v1/ocr,/parse"
    ocr_sdk_entrypoint: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "translategemma:12b-it-q4_K_M"
    render_dpi: int = 350
    output_dir: str = "outputs"
    http_timeout_sec: float = 5.0

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    @property
    def ocr_parse_path_list(self) -> list[str]:
        paths: list[str] = []
        for item in self.ocr_parse_paths.split(","):
            path = item.strip()
            if not path:
                continue
            if not path.startswith("/"):
                path = f"/{path}"
            paths.append(path)
        return paths or ["/ocr"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
