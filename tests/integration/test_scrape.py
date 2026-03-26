"""Integration tests for scrape operations.

These hit the real Olostep API and consume credits.
Requires OLOSTEP_API_KEY in the environment or .env file.
"""

from __future__ import annotations

import pytest

from src.scrape_api import run_scrape, run_scrape_get


pytestmark = pytest.mark.integration


class TestScrapeCreate:
    @pytest.mark.asyncio
    async def test_scrape_markdown(self, api):
        result = await run_scrape(
            api,
            url_to_scrape="https://example.com",
            formats=["markdown"],
        )
        assert result["id"].startswith("scrape_")
        assert result["retrieve_id"]
        assert result["result"]["markdown_content"]
        assert result["result"]["page_metadata"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_scrape_multiple_formats(self, api):
        result = await run_scrape(
            api,
            url_to_scrape="https://example.com",
            formats=["markdown", "html"],
        )
        assert result["id"].startswith("scrape_")
        assert result["result"]["markdown_content"]
        assert result["result"]["html_content"]

    @pytest.mark.asyncio
    async def test_scrape_docs_page(self, api):
        result = await run_scrape(
            api,
            url_to_scrape="https://docs.olostep.com/get-started/welcome",
            formats=["markdown"],
        )
        assert result["id"].startswith("scrape_")
        assert "olostep" in result["result"]["markdown_content"].lower()

    @pytest.mark.asyncio
    async def test_scrape_screenshot(self, api):
        result = await run_scrape(
            api,
            url_to_scrape="https://www.olostep.com",
            formats=["screenshot"],
        )
        assert result["id"].startswith("scrape_")
        assert result["result"]["screenshot_hosted_url"]


class TestScrapeGet:
    @pytest.mark.asyncio
    async def test_get_existing_scrape(self, api):
        created = await run_scrape(
            api,
            url_to_scrape="https://example.com",
            formats=["markdown"],
        )
        scrape_id = created["id"]

        fetched = await run_scrape_get(api, scrape_id)
        assert fetched["id"] == scrape_id
        assert fetched["url"] == "https://example.com"
