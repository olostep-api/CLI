"""Integration tests for map operations.

These hit the real Olostep API and consume credits.
Requires OLOSTEP_API_KEY in the environment or .env file.
"""

from __future__ import annotations

import pytest

from src.map_api import run_map


pytestmark = pytest.mark.integration


class TestMap:
    @pytest.mark.asyncio
    async def test_map_basic(self, api):
        result = await run_map(api, "https://docs.olostep.com", top_n=10)
        assert result["id"].startswith("map_")
        assert result["urls_count"] > 0
        assert len(result["urls"]) > 0
        assert all(url.startswith("http") for url in result["urls"])

    @pytest.mark.asyncio
    async def test_map_with_search_query(self, api):
        result = await run_map(
            api,
            "https://docs.olostep.com",
            search_query="scrape",
            top_n=5,
        )
        assert result["id"].startswith("map_")
        assert result["urls_count"] > 0

    @pytest.mark.asyncio
    async def test_map_with_include_urls(self, api):
        result = await run_map(
            api,
            "https://docs.olostep.com",
            include_urls=["/features/**"],
            top_n=10,
        )
        assert result["id"].startswith("map_")
        assert result["urls_count"] > 0

    @pytest.mark.asyncio
    async def test_map_with_include_and_exclude_urls(self, api):
        result = await run_map(
            api,
            "https://docs.olostep.com",
            include_urls=["/features/**"],
            exclude_urls=["/features/agents/**"],
            top_n=10,
        )
        assert result["id"].startswith("map_")
        urls = result.get("urls", [])
        for url in urls:
            assert "/features/agents/" not in url

    @pytest.mark.asyncio
    async def test_map_example_dot_com(self, api):
        result = await run_map(api, "https://example.com")
        assert result["id"].startswith("map_")
