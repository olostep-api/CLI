"""Unit tests for CLI argument parsing and validation using Typer's CliRunner.

These tests mock the API layer so no real HTTP calls are made.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _mock_api():
    return patch("main._make_api")


def _mock_token(token: str = "fake-token"):
    return patch("main._get_token", return_value=token)


class TestMapCommand:
    def test_help(self):
        result = runner.invoke(app, ["map", "--help"])
        assert result.exit_code == 0
        assert "Website URL to map" in result.output
        assert "Examples:" in result.output
        assert "olostep map" in result.output

    def test_legacy_limit_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(app, ["map", "https://example.com", "--limit", "10"])
        assert result.exit_code != 0
        assert "removed" in result.output.lower() or "limit" in result.output.lower()

    def test_top_n_zero_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(app, ["map", "https://example.com", "--top-n", "0"])
        assert result.exit_code != 0

    def test_successful_map(self):
        fake_response = {"id": "map_abc", "urls": ["https://example.com/a"]}
        with _mock_api() as mock_api_fn, tempfile.TemporaryDirectory() as d:
            api = AsyncMock()
            api.create_map = AsyncMock(return_value=fake_response)
            mock_api_fn.return_value = api
            out_path = str(Path(d) / "map.json")
            result = runner.invoke(
                app, ["map", "https://example.com", "--top-n", "5", "--out", out_path]
            )
        assert result.exit_code == 0


    def test_stdout_output(self):
        fake_response = {"id": "map_abc", "urls": ["https://example.com/a"]}
        with _mock_api() as mock_api_fn:
            api = AsyncMock()
            api.create_map = AsyncMock(return_value=fake_response)
            mock_api_fn.return_value = api
            result = runner.invoke(app, ["map", "https://example.com", "--out", "-"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed == fake_response


class TestScrapeCommand:
    def test_help(self):
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "URL to scrape" in result.output
        assert "Examples:" in result.output
        assert "olostep scrape" in result.output

    def test_invalid_format_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app,
                ["scrape", "https://example.com", "--formats", "banana"],
            )
        assert result.exit_code != 0

    def test_negative_wait_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app,
                [
                    "scrape",
                    "https://example.com",
                    "--wait-before-scraping",
                    "-1",
                ],
            )
        assert result.exit_code != 0

    def test_successful_scrape(self):
        fake_response = {"id": "scrape_abc", "result": {"markdown_content": "hello"}}
        with _mock_api() as mock_api_fn, tempfile.TemporaryDirectory() as d:
            api = AsyncMock()
            api.create_scrape = AsyncMock(return_value=fake_response)
            mock_api_fn.return_value = api
            out_path = str(Path(d) / "scrape.json")
            result = runner.invoke(
                app,
                [
                    "scrape",
                    "https://example.com",
                    "--formats",
                    "markdown",
                    "--out",
                    out_path,
                ],
            )
        assert result.exit_code == 0


    def test_stdout_output(self):
        fake_response = {"id": "scrape_abc", "result": {"markdown_content": "hello"}}
        with _mock_api() as mock_api_fn:
            api = AsyncMock()
            api.create_scrape = AsyncMock(return_value=fake_response)
            mock_api_fn.return_value = api
            result = runner.invoke(
                app,
                ["scrape", "https://example.com", "--formats", "markdown", "--out", "-"],
            )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed == fake_response


class TestScrapeGetCommand:
    def test_help(self):
        result = runner.invoke(app, ["scrape-get", "--help"])
        assert result.exit_code == 0
        assert "Scrape ID" in result.output
        assert "Examples:" in result.output
        assert "olostep scrape-get" in result.output

    def test_successful_scrape_get(self):
        fake_response = {"id": "scrape_abc", "result": {"markdown_content": "hi"}}
        with _mock_api() as mock_api_fn, tempfile.TemporaryDirectory() as d:
            api = AsyncMock()
            api.get_scrape = AsyncMock(return_value=fake_response)
            mock_api_fn.return_value = api
            out_path = str(Path(d) / "scrape_get.json")
            result = runner.invoke(
                app, ["scrape-get", "scrape_abc123", "--out", out_path]
            )
        assert result.exit_code == 0


class TestAnswerCommand:
    def test_help(self):
        result = runner.invoke(app, ["answer", "--help"])
        assert result.exit_code == 0
        assert "Task/question" in result.output
        assert "Examples:" in result.output
        assert "olostep answer" in result.output

    def test_legacy_model_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app, ["answer", "What is Olostep?", "--model", "gpt-4"]
            )
        assert result.exit_code != 0
        assert "removed" in result.output.lower() or "model" in result.output.lower()


class TestCrawlCommand:
    def test_help(self):
        result = runner.invoke(app, ["crawl", "--help"])
        assert result.exit_code == 0
        assert "Start URL" in result.output
        assert "Examples:" in result.output
        assert "olostep crawl" in result.output

    def test_max_pages_zero_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app, ["crawl", "https://example.com", "--max-pages", "0"]
            )
        assert result.exit_code != 0

    def test_negative_max_depth_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app, ["crawl", "https://example.com", "--max-depth", "-1"]
            )
        assert result.exit_code != 0

    def test_invalid_crawl_format_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app,
                ["crawl", "https://example.com", "--formats", "pdf"],
            )
        assert result.exit_code != 0

    def test_zero_poll_seconds_rejected(self):
        with _mock_api() as mock:
            mock.return_value = AsyncMock()
            result = runner.invoke(
                app, ["crawl", "https://example.com", "--poll-seconds", "0"]
            )
        assert result.exit_code != 0

    def test_dry_run_prints_payload_and_exits(self):
        result = runner.invoke(
            app,
            [
                "crawl", "https://example.com",
                "--max-pages", "10",
                "--max-depth", "3",
                "--formats", "markdown,html",
                "--search-query", "docs",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["start_url"] == "https://example.com"
        assert payload["max_pages"] == 10
        assert payload["max_depth"] == 3
        assert payload["search_query"] == "docs"
        assert payload["_retrieve_formats"] == ["markdown", "html"]

    def test_dry_run_does_not_require_api_key(self):
        result = runner.invoke(
            app, ["crawl", "https://example.com", "--dry-run"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["start_url"] == "https://example.com"

    def test_dry_run_omits_none_fields(self):
        result = runner.invoke(
            app, ["crawl", "https://example.com", "--dry-run"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert "max_depth" not in payload
        assert "webhook" not in payload
        assert "search_query" not in payload

    def test_dry_run_still_validates(self):
        result = runner.invoke(
            app,
            ["crawl", "https://example.com", "--max-pages", "0", "--dry-run"],
        )
        assert result.exit_code != 0


class TestBatchScrapeCommand:
    def test_help(self):
        result = runner.invoke(app, ["batch-scrape", "--help"])
        assert result.exit_code == 0
        assert "CSV" in result.output
        assert "Examples:" in result.output
        assert "olostep batch-scrape" in result.output

    def test_invalid_format_rejected(self):
        with _mock_token():
            result = runner.invoke(
                app, ["batch-scrape", "data.csv", "--formats", "pdf"]
            )
        assert result.exit_code != 0

    def test_zero_poll_seconds_rejected(self):
        with _mock_token():
            result = runner.invoke(
                app,
                ["batch-scrape", "data.csv", "--formats", "markdown", "--poll-seconds", "0"],
            )
        assert result.exit_code != 0

    def test_zero_items_limit_rejected(self):
        with _mock_token():
            result = runner.invoke(
                app,
                ["batch-scrape", "data.csv", "--formats", "markdown", "--items-limit", "0"],
            )
        assert result.exit_code != 0

    def test_dry_run_prints_payload_and_exits(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("custom_id,url\nitem-1,https://a.com\nitem-2,https://b.com\n")
            csv_path = f.name
        try:
            result = runner.invoke(
                app,
                ["batch-scrape", csv_path, "--formats", "markdown,html", "--country", "US", "--dry-run"],
            )
            assert result.exit_code == 0
            payload = json.loads(result.output)
            assert len(payload["items"]) == 2
            assert payload["items"][0]["url"] == "https://a.com"
            assert payload["country"] == "US"
            assert payload["_retrieve_formats"] == ["markdown", "html"]
        finally:
            Path(csv_path).unlink()

    def test_dry_run_does_not_require_api_key(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("custom_id,url\nx,https://example.com\n")
            csv_path = f.name
        try:
            result = runner.invoke(
                app, ["batch-scrape", csv_path, "--dry-run"],
            )
            assert result.exit_code == 0
            payload = json.loads(result.output)
            assert "items" in payload
        finally:
            Path(csv_path).unlink()

    def test_dry_run_with_parser_id(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("custom_id,url\nitem-1,https://a.com\n")
            csv_path = f.name
        try:
            result = runner.invoke(
                app,
                ["batch-scrape", csv_path, "--parser-id", "my-parser", "--dry-run"],
            )
            assert result.exit_code == 0
            payload = json.loads(result.output)
            assert payload["parser"] == {"id": "my-parser"}
        finally:
            Path(csv_path).unlink()


class TestLoginCommand:
    def test_help(self):
        result = runner.invoke(app, ["login", "--help"])
        assert result.exit_code == 0
        assert "browser" in result.output.lower() or "authorize" in result.output.lower()

    def test_login_writes_env(self):
        with patch("main.run_browser_login", return_value="k_test_123") as mock_login, tempfile.TemporaryDirectory() as d:
            env_p = Path(d) / ".env"
            result = runner.invoke(
                app,
                [
                    "login",
                    "--no-browser",
                    "--env-file",
                    str(env_p),
                ],
            )
            assert result.exit_code == 0
            mock_login.assert_called_once()
            text = env_p.read_text(encoding="utf-8")
            assert "OLOSTEP_API_KEY=k_test_123" in text

    def test_login_writes_credentials_json(self):
        with patch("main.run_browser_login", return_value="k_cred_99") as mock_login, tempfile.TemporaryDirectory() as d:
            cred = Path(d) / "credentials.json"
            with patch("main.get_credentials_path", return_value=cred):
                result = runner.invoke(
                    app,
                    [
                        "login",
                        "--no-browser",
                    ],
                )
            assert result.exit_code == 0
            mock_login.assert_called_once()
            data = json.loads(cred.read_text(encoding="utf-8"))
            assert data["api_key"] == "k_cred_99"


class TestBatchUpdateCommand:
    def test_help(self):
        result = runner.invoke(app, ["batch-update", "--help"])
        assert result.exit_code == 0
        assert "Batch ID" in result.output
        assert "Examples:" in result.output
        assert "olostep batch-update" in result.output

    def test_no_metadata_rejected(self):
        with _mock_token():
            result = runner.invoke(app, ["batch-update", "batch_abc"])
        assert result.exit_code != 0

    def test_invalid_metadata_json_rejected(self):
        with _mock_token():
            result = runner.invoke(
                app,
                ["batch-update", "batch_abc", "--metadata-json", "not json"],
            )
        assert result.exit_code != 0
