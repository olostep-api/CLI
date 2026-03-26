"""Integration tests for answer operations.

These hit the real Olostep API and consume credits.
Requires OLOSTEP_API_KEY in the environment or .env file.
"""

from __future__ import annotations

import json

import pytest

from src.answer_api import run_answer


pytestmark = pytest.mark.integration


class TestAnswer:
    @pytest.mark.asyncio
    async def test_answer_basic(self, api):
        result = await run_answer(
            api,
            "What is Olostep and what are its main features?",
            poll_interval_s=2.0,
            poll_timeout_s=120.0,
        )
        assert result.get("id") or result.get("answer_id")
        assert result.get("result")
        assert result["result"].get("json_content")
        assert result["result"].get("json_hosted_url")

    @pytest.mark.asyncio
    async def test_answer_with_json_format(self, api):
        result = await run_answer(
            api,
            "What is Olostep and what does it do?",
            json_format={
                "company_name": "",
                "description": "",
                "website": "",
            },
            poll_interval_s=2.0,
            poll_timeout_s=120.0,
        )
        assert result.get("id") or result.get("answer_id")
        assert result.get("result")
        assert result["result"].get("json_content") or result["result"].get("json_hosted_url")
