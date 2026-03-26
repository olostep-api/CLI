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


class TestScrapeCommand:
    def test_help(self):
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "URL to scrape" in result.output

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


class TestScrapeGetCommand:
    def test_help(self):
        result = runner.invoke(app, ["scrape-get", "--help"])
        assert result.exit_code == 0
        assert "Scrape ID" in result.output

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


class TestBatchScrapeCommand:
    def test_help(self):
        result = runner.invoke(app, ["batch-scrape", "--help"])
        assert result.exit_code == 0
        assert "CSV" in result.output

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


class TestBatchUpdateCommand:
    def test_help(self):
        result = runner.invoke(app, ["batch-update", "--help"])
        assert result.exit_code == 0
        assert "Batch ID" in result.output

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
