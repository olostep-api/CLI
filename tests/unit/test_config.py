from __future__ import annotations

import os
import platform
import tempfile
from pathlib import Path

import pytest

from config.config import (
    API_BASE_URL,
    DEFAULT_CLI_AUTH_PAGE_URL,
    DEFAULT_CLI_AUTH_PAGE_URL_DEV,
    Settings,
    ENV_API_BASE_URL,
    ENV_CLI_AUTH_PAGE_URL,
    ENV_OLOSTEP_ENV,
    get_batch_base_url,
    get_cli_auth_api_base,
    get_cli_auth_page_url,
    get_credentials_path,
    get_olostep_config_dir,
    load_env_file,
    read_credentials_api_key,
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

    def test_missing_key_raises(self, monkeypatch, tmp_path):
        old_key = os.environ.pop("OLOSTEP_API_KEY", None)
        old_tok = os.environ.pop("OLOSTEP_API_TOKEN", None)
        monkeypatch.setattr("config.config.get_credentials_path", lambda: tmp_path / "none.json")
        try:
            with pytest.raises(ValueError, match="Missing API key"):
                resolve_api_key()
        finally:
            if old_key:
                os.environ["OLOSTEP_API_KEY"] = old_key
            if old_tok:
                os.environ["OLOSTEP_API_TOKEN"] = old_tok

    def test_reads_credentials_file(self, monkeypatch, tmp_path):
        old_key = os.environ.pop("OLOSTEP_API_KEY", None)
        old_tok = os.environ.pop("OLOSTEP_API_TOKEN", None)
        cred = tmp_path / "credentials.json"
        cred.write_text('{"api_key": "from-json"}\n', encoding="utf-8")
        monkeypatch.setattr("config.config.get_credentials_path", lambda: cred)
        try:
            assert resolve_api_key() == "from-json"
        finally:
            if old_key:
                os.environ["OLOSTEP_API_KEY"] = old_key
            if old_tok:
                os.environ["OLOSTEP_API_TOKEN"] = old_tok


class TestOlostepConfigDir:
    def test_override_via_env(self, monkeypatch, tmp_path):
        d = tmp_path / "cfg"
        monkeypatch.setenv("OLOSTEP_CLI_CONFIG_DIR", str(d))
        assert get_olostep_config_dir() == d.resolve()

    def test_darwin_layout(self, monkeypatch):
        monkeypatch.delenv("OLOSTEP_CLI_CONFIG_DIR", raising=False)
        monkeypatch.setenv("HOME", "/Users/fakeuser")
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        assert get_olostep_config_dir() == Path(
            "/Users/fakeuser/Library/Application Support/olostep-cli"
        )

    def test_windows_layout(self, monkeypatch):
        monkeypatch.delenv("OLOSTEP_CLI_CONFIG_DIR", raising=False)
        fake_home = Path(r"C:\Users\fakeuser")
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        assert get_olostep_config_dir() == fake_home / "AppData" / "Roaming" / "olostep-cli"

    def test_linux_layout(self, monkeypatch):
        monkeypatch.delenv("OLOSTEP_CLI_CONFIG_DIR", raising=False)
        monkeypatch.setenv("HOME", "/home/fakeuser")
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        assert get_olostep_config_dir() == Path("/home/fakeuser/.config/olostep-cli")

    def test_credentials_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OLOSTEP_CLI_CONFIG_DIR", str(tmp_path))
        assert get_credentials_path() == tmp_path.resolve() / "credentials.json"


class TestReadCredentialsApiKey:
    def test_reads_api_key_field(self, tmp_path):
        p = tmp_path / "c.json"
        p.write_text('{"api_key": "a"}\n', encoding="utf-8")
        assert read_credentials_api_key(p) == "a"

    def test_reads_camel_api_key(self, tmp_path):
        p = tmp_path / "c.json"
        p.write_text('{"apiKey": "b"}\n', encoding="utf-8")
        assert read_credentials_api_key(p) == "b"

    def test_missing_file(self, tmp_path):
        assert read_credentials_api_key(tmp_path / "nope.json") is None


class TestResolveTimeoutS:
    def test_explicit_value(self):
        assert resolve_timeout_s(30.0) == 30.0

    def test_none_returns_default(self):
        assert resolve_timeout_s(None) == DEFAULT_HTTP_TIMEOUT_S


class TestGetCliAuthUrls:
    def test_api_base_default(self):
        old = os.environ.pop(ENV_API_BASE_URL, None)
        try:
            assert get_cli_auth_api_base() == API_BASE_URL
        finally:
            if old is not None:
                os.environ[ENV_API_BASE_URL] = old

    def test_api_base_from_env(self):
        old = os.environ.get(ENV_API_BASE_URL)
        os.environ[ENV_API_BASE_URL] = "https://custom/v1"
        try:
            assert get_cli_auth_api_base() == "https://custom/v1"
        finally:
            if old is None:
                os.environ.pop(ENV_API_BASE_URL, None)
            else:
                os.environ[ENV_API_BASE_URL] = old

    def test_page_url_default(self):
        old_page = os.environ.pop(ENV_CLI_AUTH_PAGE_URL, None)
        old_olostep_env = os.environ.pop(ENV_OLOSTEP_ENV, None)
        old_env = os.environ.pop("ENV", None)
        try:
            assert get_cli_auth_page_url() == DEFAULT_CLI_AUTH_PAGE_URL
        finally:
            if old_page is not None:
                os.environ[ENV_CLI_AUTH_PAGE_URL] = old_page
            if old_olostep_env is not None:
                os.environ[ENV_OLOSTEP_ENV] = old_olostep_env
            if old_env is not None:
                os.environ["ENV"] = old_env

    def test_page_url_development_env_uses_localhost(self):
        old_page = os.environ.pop(ENV_CLI_AUTH_PAGE_URL, None)
        old_olostep_env = os.environ.get(ENV_OLOSTEP_ENV)
        os.environ[ENV_OLOSTEP_ENV] = "development"
        try:
            assert get_cli_auth_page_url() == DEFAULT_CLI_AUTH_PAGE_URL_DEV
        finally:
            if old_page is not None:
                os.environ[ENV_CLI_AUTH_PAGE_URL] = old_page
            if old_olostep_env is None:
                os.environ.pop(ENV_OLOSTEP_ENV, None)
            else:
                os.environ[ENV_OLOSTEP_ENV] = old_olostep_env

    def test_placeholder_raises(self):
        with pytest.raises(ValueError, match="placeholder"):
            get_cli_auth_api_base("<YOUR_URL>")


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
