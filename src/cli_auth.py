from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
import string
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote, urlencode

import httpx
import typer

from config.config import ENV_API_KEY, ENV_API_TOKEN

_DEFAULT_POLL_SECONDS = 3.0
_DEFAULT_TIMEOUT_S = 600.0
_REQUEST_TIMEOUT_S = 30.0
_STATUS_HINT_INTERVAL_S = 15.0

# RFC 7636: code_verifier length 43–128, unreserved characters.
_VERIFIER_ALPHABET = string.ascii_letters + string.digits + "-._~"
_VERIFIER_LENGTH = 64


class CliAuthError(RuntimeError):
    """Browser CLI auth failed (user-facing message)."""


def code_challenge_from_verifier(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_code_verifier() -> str:
    return "".join(secrets.choice(_VERIFIER_ALPHABET) for _ in range(_VERIFIER_LENGTH))


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(page_url: str, session_id: str, code_challenge: str) -> str:
    q = urlencode({"code_challenge": code_challenge})
    frag = f"session_id={quote(session_id, safe='')}"
    return f"{page_url}?{q}#{frag}"


def merge_env_api_key(path: Path, api_key: str) -> None:
    """Set OLOSTEP_API_KEY in a .env file; replace existing OLOSTEP_API_KEY or OLOSTEP_API_TOKEN line."""
    line = f"{ENV_API_KEY}={api_key}\n"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        replaced = False
        for ln in lines:
            s = ln.strip()
            if s.startswith(f"{ENV_API_KEY}=") or s.startswith(f"{ENV_API_TOKEN}="):
                if not replaced:
                    out.append(line)
                    replaced = True
                continue
            out.append(ln)
        if not replaced:
            if out and not out[-1].endswith("\n"):
                out.append("\n")
            out.append(line)
        path.write_text("".join(out), encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(line, encoding="utf-8")


def save_credentials_json(path: Path, api_key: str) -> None:
    """Write `{"api_key": "..."}` to the user credentials file; restrict permissions on Unix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"api_key": api_key}, indent=2) + "\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass


def poll_status_until_complete(
    api_base: str,
    session_id: str,
    code_verifier: str,
    *,
    poll_seconds: float,
    timeout_s: float,
    request_timeout_s: float = _REQUEST_TIMEOUT_S,
    verbose: bool = False,
) -> str:
    deadline = time.monotonic() + timeout_s
    last_network_error = ""
    start = time.monotonic()
    last_hint = start
    user_notified_network = False
    user_notified_poll_wait = False
    hinted_session_missing = False
    with httpx.Client(base_url=api_base, timeout=request_timeout_s) as client:
        while time.monotonic() < deadline:
            try:
                r = client.post(
                    "/cli-auth-status",
                    json={"session_id": session_id, "code_verifier": code_verifier},
                )
            except httpx.RequestError as exc:
                last_network_error = str(exc)
                if verbose and not user_notified_network:
                    typer.secho(
                        "  … Checking Olostep API (retrying on network issues)…",
                        dim=True,
                    )
                    user_notified_network = True
                time.sleep(poll_seconds)
                continue

            if r.status_code == 403:
                raise CliAuthError(
                    "PKCE verification failed (session does not match this machine)."
                )
            if r.status_code == 404:
                if verbose and not hinted_session_missing:
                    typer.secho(
                        "  … Waiting for the sign-in page to register this session.",
                        dim=True,
                    )
                    typer.secho(
                        "    Open the link above in your browser if you have not yet.\n",
                        dim=True,
                    )
                    hinted_session_missing = True
                time.sleep(poll_seconds)
                continue
            if r.status_code >= 500:
                time.sleep(poll_seconds)
                continue
            if not r.is_success:
                body = (r.text or "")[:500]
                raise CliAuthError(f"Unexpected HTTP {r.status_code}: {body}")

            try:
                data = r.json()
            except ValueError as exc:
                raise CliAuthError(f"Invalid JSON from /status: {exc}") from exc

            status = data.get("status")
            if status == "complete":
                key = data.get("apiKey") or data.get("api_key")
                if not key:
                    raise CliAuthError("Authorization complete but response had no apiKey.")
                if verbose:
                    typer.secho("  ✓  Verified — Olostep returned your API key.\n", fg="green", bold=True)
                return str(key)
            if status == "pending":
                now = time.monotonic()
                if verbose:
                    if not user_notified_poll_wait:
                        typer.secho(
                            "\n  Checking authorization status with Olostep…",
                            fg="cyan",
                            bold=True,
                        )
                        typer.secho(
                            '  Sign in and click "Authorize" in your browser. '
                            "This terminal will update when you are done.\n",
                            dim=True,
                        )
                        user_notified_poll_wait = True
                        last_hint = now
                    elif now - last_hint >= _STATUS_HINT_INTERVAL_S:
                        elapsed = int(now - start)
                        typer.secho(
                            f"  … Still waiting ({elapsed}s). Complete the steps in your browser.\n",
                            dim=True,
                        )
                        last_hint = now
                time.sleep(poll_seconds)
                continue
            raise CliAuthError(f"Unexpected status in response: {data!r}")

    msg = f"Timed out after {timeout_s:.0f}s waiting for browser authorization."
    if last_network_error:
        msg += f" Last network error: {last_network_error}"
    raise CliAuthError(msg)


def run_browser_login(
    *,
    api_base: str,
    page_url: str,
    poll_seconds: float = _DEFAULT_POLL_SECONDS,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    no_browser: bool = False,
    verbose: bool = True,
) -> str:
    """
    Open authorize page, poll /status, return API key (does not write .env).
    """
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be > 0")
    if timeout_s <= 0:
        raise ValueError("timeout_s must be > 0")

    code_verifier = generate_code_verifier()
    code_challenge = code_challenge_from_verifier(code_verifier)
    session_id = generate_session_id()
    url = build_authorize_url(page_url, session_id, code_challenge)

    skip_browser = no_browser or os.environ.get("NO_BROWSER", "").strip() == "1"

    if verbose:
        typer.secho("")
        typer.secho(
            "  ┌─────────────────────────────────────────────────────────┐",
            fg="bright_blue",
        )
        typer.secho(
            "  │  Olostep CLI · browser sign-in                          │",
            fg="bright_blue",
            bold=True,
        )
        typer.secho(
            "  └─────────────────────────────────────────────────────────┘",
            fg="bright_blue",
        )
        typer.secho("")
        typer.secho("  Your sign-in link", bold=True)
        typer.secho(f"  {url}\n", fg="cyan")
        if skip_browser:
            typer.secho(
                "  → No browser launch (--no-browser). Open the URL above manually.\n",
                fg="yellow",
            )
        else:
            typer.secho("  → Requesting default browser…", fg="yellow")
            webbrowser.open(url)
            typer.secho(
                "  → Browser open request sent. Use the window that appeared, or paste the link.",
                dim=True,
            )
            typer.secho(
                "  → If nothing opened, copy the link from above.\n",
                dim=True,
            )
    else:
        if skip_browser:
            typer.echo(url)
        else:
            webbrowser.open(url)

    return poll_status_until_complete(
        api_base,
        session_id,
        code_verifier,
        poll_seconds=poll_seconds,
        timeout_s=timeout_s,
        verbose=verbose,
    )
