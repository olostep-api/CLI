from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from config.config import ENV_API_KEY, ENV_API_TOKEN
from src.cli_auth import (
    CliAuthError,
    build_authorize_url,
    code_challenge_from_verifier,
    merge_env_api_key,
    poll_status_until_complete,
    save_credentials_json,
)


class TestPkce:
    def test_code_challenge_matches_sha256_base64url(self):
        verifier = "a" * 43  # minimum PKCE length
        raw = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
        assert code_challenge_from_verifier(verifier) == expected
        assert "=" not in code_challenge_from_verifier(verifier)


class TestBuildAuthorizeUrl:
    def test_shape(self):
        u = build_authorize_url(
            "https://www.olostep.com/cli-auth",
            "sid_abc",
            "challengex",
        )
        assert u.startswith("https://www.olostep.com/cli-auth?")
        assert "code_challenge=challengex" in u
        assert u.endswith("#session_id=sid_abc")


class TestSaveCredentialsJson:
    def test_writes_api_key(self, tmp_path: Path):
        p = tmp_path / "credentials.json"
        save_credentials_json(p, "secret-key")
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data == {"api_key": "secret-key"}


class TestMergeEnvApiKey:
    def test_creates_file(self, tmp_path: Path):
        p = tmp_path / ".env"
        merge_env_api_key(p, "secret")
        assert p.read_text(encoding="utf-8") == f"{ENV_API_KEY}=secret\n"

    def test_replaces_api_key(self, tmp_path: Path):
        p = tmp_path / ".env"
        p.write_text(f"{ENV_API_KEY}=old\nFOO=bar\n", encoding="utf-8")
        merge_env_api_key(p, "new")
        text = p.read_text(encoding="utf-8")
        assert f"{ENV_API_KEY}=new" in text
        assert "old" not in text
        assert "FOO=bar" in text

    def test_replaces_token_line_with_api_key(self, tmp_path: Path):
        p = tmp_path / ".env"
        p.write_text(f"{ENV_API_TOKEN}=tok\n", encoding="utf-8")
        merge_env_api_key(p, "keyval")
        assert p.read_text(encoding="utf-8") == f"{ENV_API_KEY}=keyval\n"


def _httpx_client_with_mock_transport(handler):
    """Patch cli_auth.httpx.Client to use MockTransport without recursive patch."""
    RealClient = httpx.Client

    def fake_client(*args, **kwargs):
        kw = dict(kwargs)
        kw["transport"] = httpx.MockTransport(handler)
        return RealClient(*args, **kw)

    return fake_client


class TestPollStatus:
    def test_pending_then_complete(self):
        n = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal n
            n += 1
            if n == 1:
                return httpx.Response(200, json={"status": "pending"})
            return httpx.Response(200, json={"status": "complete", "apiKey": "fc_ok"})

        with patch(
            "src.cli_auth.httpx.Client",
            side_effect=_httpx_client_with_mock_transport(handler),
        ):
            key = poll_status_until_complete(
                "https://api.example/v1",
                "sid",
                "ver",
                poll_seconds=0.01,
                timeout_s=5.0,
                request_timeout_s=5.0,
            )
        assert key == "fc_ok"

    def test_403_raises(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={})

        with patch(
            "src.cli_auth.httpx.Client",
            side_effect=_httpx_client_with_mock_transport(handler),
        ):
            with pytest.raises(CliAuthError, match="PKCE"):
                poll_status_until_complete(
                    "https://api.example/v1",
                    "sid",
                    "ver",
                    poll_seconds=0.01,
                    timeout_s=2.0,
                    request_timeout_s=5.0,
                )
