from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import ENV_API_KEY, ENV_API_TOKEN, load_env_file


def _resolve_key() -> str | None:
    load_env_file()
    return (os.getenv(ENV_API_KEY) or os.getenv(ENV_API_TOKEN) or "").strip() or None


@pytest.fixture(scope="session")
def api_key() -> str:
    key = _resolve_key()
    if not key:
        pytest.skip("OLOSTEP_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="session")
def api(api_key: str):
    from src.api_client import OlostepAPI

    return OlostepAPI(
        api_key=api_key,
        base_url="https://api.olostep.com/v1",
        timeout_s=60.0,
    )
