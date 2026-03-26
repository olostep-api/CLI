"""Integration tests for crawl operations.

These hit the real Olostep API and consume credits.
Requires OLOSTEP_API_KEY in the environment or .env file.
"""

from __future__ import annotations

import pytest

from src.crawl_api import run_crawl


pytestmark = pytest.mark.integration


class TestCrawl:
    @pytest.mark.asyncio
    async def test_crawl_basic(self, api):
        result = await run_crawl(
            api,
            start_url="https://example.com",
            max_pages=3,
            retrieve_formats=["markdown"],
            poll_seconds=3.0,
            poll_timeout_s=120.0,
        )
        assert result["crawl_id"]
        assert result["crawl"]["status"] == "completed"
        assert result["results_count"] >= 1
        assert len(result["results"]) >= 1

        first_page = result["results"][0]
        assert "page" in first_page
        assert "retrieved" in first_page
        assert first_page["retrieved"].get("markdown_content") or first_page["retrieved"].get("success")

    @pytest.mark.asyncio
    async def test_crawl_with_depth_limit(self, api):
        result = await run_crawl(
            api,
            start_url="https://docs.olostep.com",
            max_pages=5,
            max_depth=1,
            retrieve_formats=["markdown"],
            poll_seconds=3.0,
            poll_timeout_s=180.0,
        )
        assert result["crawl_id"]
        assert result["crawl"]["status"] == "completed"
        assert result["results_count"] >= 1

    @pytest.mark.asyncio
    async def test_crawl_with_url_filters(self, api):
        result = await run_crawl(
            api,
            start_url="https://docs.olostep.com",
            max_pages=5,
            max_depth=2,
            include_urls=["/features/**", "/get-started/**"],
            exclude_urls=["/changelog/**"],
            retrieve_formats=["markdown"],
            poll_seconds=3.0,
            poll_timeout_s=180.0,
        )
        assert result["crawl_id"]
        assert result["crawl"]["status"] == "completed"
        assert result["results_count"] >= 1

    @pytest.mark.asyncio
    async def test_crawl_multiple_formats(self, api):
        result = await run_crawl(
            api,
            start_url="https://example.com",
            max_pages=2,
            retrieve_formats=["markdown", "html"],
            poll_seconds=3.0,
            poll_timeout_s=120.0,
        )
        assert result["crawl_id"]
        assert result["results_count"] >= 1
        first_retrieved = result["results"][0].get("retrieved", {})
        assert first_retrieved.get("markdown_content") or first_retrieved.get("success")
