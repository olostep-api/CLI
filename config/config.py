from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Final

ENV_FILE_NAME: Final = ".env"
ENV_API_KEY: Final = "OLOSTEP_API_KEY"
ENV_API_TOKEN: Final = "OLOSTEP_API_TOKEN"

DEFAULT_HTTP_TIMEOUT_S: Final = 60.0
API_BASE_URL: Final = "https://api.olostep.com/v1"
BATCH_BASE_URL: Final = "https://api.olostep.com"
DEFAULT_ANSWER_POLL_INTERVAL_S: Final = 1.5
DEFAULT_ANSWER_POLL_TIMEOUT_S: Final = 300.0
DEFAULT_BATCH_POLL_SECONDS: Final = 5.0
DEFAULT_BATCH_LOG_EVERY: Final = 1
DEFAULT_BATCH_ITEMS_LIMIT: Final = 50
DEFAULT_BATCH_FORMATS: Final = "markdown"
DEFAULT_RETRIEVE_FORMATS: Final = ("markdown",)
DEFAULT_SCRAPE_FORMATS: Final = "markdown"
DEFAULT_MAP_OUT_PATH: Final = "output/map.json"
DEFAULT_ANSWER_OUT_PATH: Final = "output/answer.json"
DEFAULT_BATCH_OUT_PATH: Final = "output/batch_results.json"
DEFAULT_SCRAPE_OUT_PATH: Final = "output/scrape.json"
DEFAULT_SCRAPE_GET_OUT_PATH: Final = "output/scrape_get.json"
DEFAULT_BATCH_UPDATE_OUT_PATH: Final = "output/batch_update.json"
DEFAULT_CRAWL_OUT_PATH: Final = "output/crawl_results.json"
DEFAULT_CRAWL_MAX_PAGES: Final = 50
DEFAULT_CRAWL_POLL_SECONDS: Final = 5.0
DEFAULT_CRAWL_POLL_TIMEOUT_S: Final = 900.0
DEFAULT_CRAWL_PAGES_LIMIT: Final = 50
DEFAULT_CRAWL_FORMATS: Final = "markdown"
RETRIEVE_FORMATS_ALLOWED: Final = ("markdown", "html", "json")
SCRAPE_FORMATS_ALLOWED: Final = ("html", "markdown", "text", "json", "raw_pdf", "screenshot")
BATCH_RETRIEVE_PROGRESS_LOG_EVERY: Final = 50

PROJECT_ROOT: Final = Path(__file__).resolve().parents[1]
ENV_PATH: Final = PROJECT_ROOT / ENV_FILE_NAME


def _strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _is_placeholder(value: str) -> bool:
    value = value.strip()
    return value.startswith("<") and value.endswith(">")


def load_env_file(path: Path = ENV_PATH) -> None:
    """
    Lightweight .env reader. Existing process env vars win over file values.
    """
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, _strip_wrapping_quotes(value))


def resolve_api_key(api_key: str | None = None) -> str:
    load_env_file()
    key = (api_key or os.getenv(ENV_API_KEY) or os.getenv(ENV_API_TOKEN) or "").strip()
    if not key:
        raise ValueError(
            f"Missing API key. Set {ENV_API_KEY} or {ENV_API_TOKEN} in environment/.env."
        )
    return key


def resolve_timeout_s(timeout_s: float | None = None) -> float:
    if timeout_s is not None:
        return float(timeout_s)
    return DEFAULT_HTTP_TIMEOUT_S


def get_batch_base_url(explicit_base_url: str | None = None) -> str:
    if explicit_base_url and explicit_base_url.strip():
        resolved = explicit_base_url.strip().rstrip("/")
        if _is_placeholder(resolved):
            raise ValueError(
                f"Invalid batch base URL placeholder: {resolved}."
            )
        return resolved

    return BATCH_BASE_URL


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    timeout_s: float = DEFAULT_HTTP_TIMEOUT_S

    @staticmethod
    def from_env(
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
    ) -> "Settings":
        key = resolve_api_key(api_key)
        resolved_base_url = (base_url or API_BASE_URL).strip().rstrip("/")
        if not resolved_base_url:
            raise ValueError("Missing API base URL in config.")
        if _is_placeholder(resolved_base_url):
            raise ValueError(
                f"Invalid API base URL placeholder: {resolved_base_url}."
            )
        return Settings(
            api_key=key,
            base_url=resolved_base_url,
            timeout_s=resolve_timeout_s(timeout_s),
        )
