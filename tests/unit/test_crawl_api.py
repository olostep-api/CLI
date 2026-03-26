from __future__ import annotations

import pytest

from src.crawl_api import build_crawl_payload, parse_crawl_retrieve_formats


class TestParseCrawlRetrieveFormats:
    def test_single_format(self):
        assert parse_crawl_retrieve_formats("markdown") == ["markdown"]

    def test_multiple_formats(self):
        assert parse_crawl_retrieve_formats("markdown,html,json") == [
            "markdown",
            "html",
            "json",
        ]

    def test_strips_whitespace(self):
        assert parse_crawl_retrieve_formats(" html , json ") == ["html", "json"]

    def test_case_insensitive(self):
        assert parse_crawl_retrieve_formats("Markdown") == ["markdown"]

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="At least one format"):
            parse_crawl_retrieve_formats("")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid format"):
            parse_crawl_retrieve_formats("markdown,pdf")

    def test_screenshot_not_allowed(self):
        with pytest.raises(ValueError, match="Invalid format"):
            parse_crawl_retrieve_formats("screenshot")


class TestBuildCrawlPayload:
    def test_minimal(self):
        payload = build_crawl_payload(start_url="https://example.com", max_pages=10)
        assert payload == {"start_url": "https://example.com", "max_pages": 10}

    def test_with_max_depth(self):
        payload = build_crawl_payload(
            start_url="https://example.com", max_pages=5, max_depth=2
        )
        assert payload["max_depth"] == 2

    def test_with_include_subdomain(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=5,
            include_subdomain=True,
        )
        assert payload["include_subdomain"] is True

    def test_with_include_external(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=5,
            include_external=False,
        )
        assert payload["include_external"] is False

    def test_with_url_filters(self):
        payload = build_crawl_payload(
            start_url="https://docs.olostep.com",
            max_pages=10,
            include_urls=["/features/**"],
            exclude_urls=["/changelog/**"],
        )
        assert payload["include_urls"] == ["/features/**"]
        assert payload["exclude_urls"] == ["/changelog/**"]

    def test_with_search_query_and_top_n(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=20,
            search_query="API docs",
            top_n=5,
        )
        assert payload["search_query"] == "API docs"
        assert payload["top_n"] == 5

    def test_with_webhook(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=5,
            webhook="https://hooks.example.com/done",
        )
        assert payload["webhook"] == "https://hooks.example.com/done"

    def test_with_timeout(self):
        payload = build_crawl_payload(
            start_url="https://example.com", max_pages=5, timeout=120
        )
        assert payload["timeout"] == 120

    def test_with_follow_robots_txt(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=5,
            follow_robots_txt=False,
        )
        assert payload["follow_robots_txt"] is False

    def test_none_optionals_excluded(self):
        payload = build_crawl_payload(
            start_url="https://example.com",
            max_pages=5,
            max_depth=None,
            include_subdomain=None,
            webhook=None,
        )
        assert "max_depth" not in payload
        assert "include_subdomain" not in payload
        assert "webhook" not in payload
