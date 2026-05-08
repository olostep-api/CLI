from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ENV_FILE_NAME: Final = ".env"
ENV_API_KEY: Final = "OLOSTEP_API_KEY"
ENV_API_TOKEN: Final = "OLOSTEP_API_TOKEN"
ENV_API_BASE_URL: Final = "OLOSTEP_API_BASE_URL"
ENV_CLI_AUTH_PAGE_URL: Final = "OLOSTEP_CLI_AUTH_PAGE_URL"
ENV_CLI_CONFIG_DIR: Final = "OLOSTEP_CLI_CONFIG_DIR"
ENV_OLOSTEP_ENV: Final = "OLOSTEP_ENV"
ENV_GENERIC_ENV: Final = "ENV"
CREDENTIALS_FILE_NAME: Final = "credentials.json"

DEFAULT_HTTP_TIMEOUT_S: Final = 60.0
API_BASE_URL: Final = "https://api.olostep.com/v1"
DEFAULT_CLI_AUTH_PAGE_URL: Final = "https://www.olostep.com/cli-auth"
DEFAULT_CLI_AUTH_PAGE_URL_DEV: Final = "http://localhost:1660/cli-auth"
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

def _resolve_project_root() -> Path:
    """Resolve runtime root for source and frozen builds.

    In PyInstaller one-file mode, bundled data files are extracted under
    ``sys._MEIPASS`` at runtime. Prefer that location when present so bundled
    assets (for example, ``skills/``) are discoverable.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT: Final = _resolve_project_root()
ENV_PATH: Final = PROJECT_ROOT / ENV_FILE_NAME


def get_olostep_config_dir() -> Path:
    """
    Per-user config directory (matches typical Node `os.platform()` layout).

    - macOS: ~/Library/Application Support/olostep-cli
    - Windows: ~/AppData/Roaming/olostep-cli
    - Linux and others: ~/.config/olostep-cli

    Override with OLOSTEP_CLI_CONFIG_DIR (e.g. for tests).
    """
    override = os.getenv(ENV_CLI_CONFIG_DIR, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "olostep-cli"
    if system == "Windows":
        return home / "AppData" / "Roaming" / "olostep-cli"
    return home / ".config" / "olostep-cli"


def get_credentials_path() -> Path:
    """Path to credentials JSON written by `olostep login` (default)."""
    return get_olostep_config_dir() / CREDENTIALS_FILE_NAME


def read_credentials_api_key(path: Path | None = None) -> str | None:
    """Read api_key from credentials.json; returns None if missing or invalid."""
    p = path or get_credentials_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    v = (data.get("api_key") or data.get("apiKey") or "").strip()
    return v or None


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
    if key:
        return key
    cred = read_credentials_api_key()
    if cred:
        return cred
    raise ValueError(
        f"Missing API key. Set {ENV_API_KEY} or {ENV_API_TOKEN}, add a project `.env`, "
        f"or run `olostep login` (saves {CREDENTIALS_FILE_NAME} under the app config directory)."
    )


def resolve_timeout_s(timeout_s: float | None = None) -> float:
    if timeout_s is not None:
        return float(timeout_s)
    return DEFAULT_HTTP_TIMEOUT_S


def get_cli_auth_api_base(explicit: str | None = None) -> str:
    """API root for CLI browser auth (`/status`, etc.); does not require an API key."""
    raw = (explicit or os.getenv(ENV_API_BASE_URL) or API_BASE_URL).strip().rstrip("/")
    if not raw:
        raise ValueError("Missing CLI auth API base URL.")
    if _is_placeholder(raw):
        raise ValueError(f"Invalid CLI auth API base URL placeholder: {raw}.")
    return raw


def _default_cli_auth_page_url_for_environment() -> str:
    """Production www URL unless OLOSTEP_ENV/ENV is development-like (matches local Next dev server)."""
    mode = (
        os.getenv(ENV_OLOSTEP_ENV) or os.getenv(ENV_GENERIC_ENV) or ""
    ).strip().lower()
    if mode in ("development", "dev", "local"):
        return DEFAULT_CLI_AUTH_PAGE_URL_DEV
    return DEFAULT_CLI_AUTH_PAGE_URL


def get_cli_auth_page_url(explicit: str | None = None) -> str:
    """Authorize page URL opened in the browser (query + hash appended by the CLI)."""
    if explicit and explicit.strip():
        raw = explicit.strip().rstrip("/")
    else:
        from_env = os.getenv(ENV_CLI_AUTH_PAGE_URL, "").strip()
        if from_env:
            raw = from_env.rstrip("/")
        else:
            raw = _default_cli_auth_page_url_for_environment().rstrip("/")
    if not raw:
        raise ValueError("Missing CLI auth page URL.")
    if _is_placeholder(raw):
        raise ValueError(f"Invalid CLI auth page URL placeholder: {raw}.")
    return raw


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
