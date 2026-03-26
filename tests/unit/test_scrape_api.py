from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.scrape_api import build_scrape_payload, load_payload_object, parse_scrape_formats


class TestParseScrapeFormats:
    def test_single_format(self):
        assert parse_scrape_formats("markdown") == ["markdown"]

    def test_multiple_formats(self):
        result = parse_scrape_formats("markdown,html,text")
        assert result == ["markdown", "html", "text"]

    def test_all_allowed_formats(self):
        result = parse_scrape_formats("html,markdown,text,json,raw_pdf,screenshot")
        assert len(result) == 6

    def test_strips_whitespace(self):
        assert parse_scrape_formats("  markdown , html ") == ["markdown", "html"]

    def test_case_insensitive(self):
        assert parse_scrape_formats("Markdown,HTML") == ["markdown", "html"]

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="At least one format"):
            parse_scrape_formats("")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid scrape format"):
            parse_scrape_formats("markdown,banana")


class TestBuildScrapePayload:
    def test_minimal(self):
        payload = build_scrape_payload(url_to_scrape="https://example.com")
        assert payload == {"url_to_scrape": "https://example.com"}

    def test_with_formats(self):
        payload = build_scrape_payload(
            url_to_scrape="https://example.com",
            formats=["markdown", "html"],
        )
        assert payload["formats"] == ["markdown", "html"]

    def test_with_country(self):
        payload = build_scrape_payload(
            url_to_scrape="https://example.com",
            country="US",
        )
        assert payload["country"] == "US"

    def test_with_wait(self):
        payload = build_scrape_payload(
            url_to_scrape="https://example.com",
            wait_before_scraping=2000,
        )
        assert payload["wait_before_scraping"] == 2000

    def test_payload_object_merged(self):
        payload = build_scrape_payload(
            url_to_scrape="https://example.com",
            formats=["markdown"],
            payload_object={"actions": [{"type": "wait", "milliseconds": 1000}]},
        )
        assert payload["url_to_scrape"] == "https://example.com"
        assert payload["formats"] == ["markdown"]
        assert payload["actions"] == [{"type": "wait", "milliseconds": 1000}]

    def test_url_overrides_payload_object(self):
        payload = build_scrape_payload(
            url_to_scrape="https://real.com",
            payload_object={"url_to_scrape": "https://old.com"},
        )
        assert payload["url_to_scrape"] == "https://real.com"


class TestLoadPayloadObject:
    def test_returns_empty_when_nothing_provided(self):
        assert load_payload_object() == {}

    def test_parses_json_string(self):
        result = load_payload_object(payload_json='{"key": "value"}')
        assert result == {"key": "value"}

    def test_reads_json_file(self):
        data = {"hello": "world"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            result = load_payload_object(payload_file=f.name)
        assert result == data
        Path(f.name).unlink()

    def test_both_flags_raises(self):
        with pytest.raises(ValueError, match="only one"):
            load_payload_object(payload_json="{}", payload_file="file.json")

    def test_invalid_json_string_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_payload_object(payload_json="not json")

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match="must be a JSON object"):
            load_payload_object(payload_json="[1, 2, 3]")

    def test_missing_file_raises(self):
        with pytest.raises(ValueError, match="Cannot read"):
            load_payload_object(payload_file="/nonexistent/path.json")
