from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from config.config import (
    Settings,
    get_batch_base_url,
    load_env_file,
    resolve_api_key,
    resolve_timeout_s,
    BATCH_BASE_URL,
    DEFAULT_HTTP_TIMEOUT_S,
)


class TestLoadEnvFile:
    def test_loads_key_value(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_CLI_VAR=hello\n")
            f.flush()
            os.environ.pop("TEST_CLI_VAR", None)
            load_env_file(Path(f.name))
        assert os.environ.get("TEST_CLI_VAR") == "hello"
        os.environ.pop("TEST_CLI_VAR", None)
        Path(f.name).unlink()

    def test_existing_env_wins(self):
        os.environ["TEST_CLI_EXIST"] = "original"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_CLI_EXIST=overridden\n")
            f.flush()
            load_env_file(Path(f.name))
        assert os.environ["TEST_CLI_EXIST"] == "original"
        os.environ.pop("TEST_CLI_EXIST", None)
        Path(f.name).unlink()

    def test_strips_quotes(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write('TEST_CLI_QUOTED="my_value"\n')
            f.flush()
            os.environ.pop("TEST_CLI_QUOTED", None)
            load_env_file(Path(f.name))
        assert os.environ.get("TEST_CLI_QUOTED") == "my_value"
        os.environ.pop("TEST_CLI_QUOTED", None)
        Path(f.name).unlink()

    def test_skips_comments_and_blanks(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("# comment\n\nTEST_CLI_OK=yes\n")
            f.flush()
            os.environ.pop("TEST_CLI_OK", None)
            load_env_file(Path(f.name))
        assert os.environ.get("TEST_CLI_OK") == "yes"
        os.environ.pop("TEST_CLI_OK", None)
        Path(f.name).unlink()

    def test_missing_file_is_noop(self):
        load_env_file(Path("/nonexistent/.env"))


class TestResolveApiKey:
    def test_explicit_key_wins(self):
        assert resolve_api_key("explicit-key") == "explicit-key"

    def test_missing_key_raises(self):
        old_key = os.environ.pop("OLOSTEP_API_KEY", None)
        old_tok = os.environ.pop("OLOSTEP_API_TOKEN", None)
        try:
            with pytest.raises(ValueError, match="Missing API key"):
                resolve_api_key()
        finally:
            if old_key:
                os.environ["OLOSTEP_API_KEY"] = old_key
            if old_tok:
                os.environ["OLOSTEP_API_TOKEN"] = old_tok


class TestResolveTimeoutS:
    def test_explicit_value(self):
        assert resolve_timeout_s(30.0) == 30.0

    def test_none_returns_default(self):
        assert resolve_timeout_s(None) == DEFAULT_HTTP_TIMEOUT_S


class TestGetBatchBaseUrl:
    def test_default(self):
        assert get_batch_base_url(None) == BATCH_BASE_URL

    def test_explicit_url(self):
        assert get_batch_base_url("https://custom.api.com/") == "https://custom.api.com"

    def test_placeholder_raises(self):
        with pytest.raises(ValueError, match="placeholder"):
            get_batch_base_url("<YOUR_URL>")


class TestSettings:
    def test_from_env_with_explicit_key(self):
        s = Settings.from_env(api_key="test-key")
        assert s.api_key == "test-key"
        assert s.base_url == "https://api.olostep.com/v1"
        assert s.timeout_s == DEFAULT_HTTP_TIMEOUT_S

    def test_from_env_custom_base_url(self):
        s = Settings.from_env(api_key="k", base_url="https://staging.api.com/v1/")
        assert s.base_url == "https://staging.api.com/v1"

    def test_from_env_placeholder_url_raises(self):
        with pytest.raises(ValueError, match="placeholder"):
            Settings.from_env(api_key="k", base_url="<YOUR_BASE_URL>")
