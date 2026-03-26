from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.answer_api import _FAILED_STATUSES, _SUCCESS_STATUSES, _is_done, run_answer


class TestIsDone:
    @pytest.mark.parametrize("status", sorted(_SUCCESS_STATUSES))
    def test_success_statuses_return_true(self, status):
        assert _is_done({"status": status}) is True

    @pytest.mark.parametrize("status", sorted(_FAILED_STATUSES))
    def test_failed_statuses_return_true(self, status):
        assert _is_done({"status": status}) is True

    def test_in_progress_returns_false(self):
        assert _is_done({"status": "in_progress"}) is False

    def test_missing_status_returns_false(self):
        assert _is_done({}) is False

    def test_empty_status_returns_false(self):
        assert _is_done({"status": ""}) is False

    def test_none_status_returns_false(self):
        assert _is_done({"status": None}) is False

    def test_case_insensitive(self):
        assert _is_done({"status": "COMPLETED"}) is True
        assert _is_done({"status": "Failed"}) is True


class TestRunAnswer:
    @pytest.mark.asyncio
    async def test_raises_on_failed_status(self):
        api = AsyncMock()
        api.create_answer = AsyncMock(return_value={"id": "ans_1"})
        api.get_answer = AsyncMock(return_value={"id": "ans_1", "status": "failed"})

        with pytest.raises(RuntimeError, match="status=failed"):
            await run_answer(api, "test task", poll_interval_s=0.01, poll_timeout_s=1)

    @pytest.mark.asyncio
    async def test_returns_on_success(self):
        api = AsyncMock()
        api.create_answer = AsyncMock(return_value={"id": "ans_1"})
        api.get_answer = AsyncMock(
            return_value={"id": "ans_1", "status": "completed", "result": {"text": "ok"}}
        )

        result = await run_answer(api, "test task", poll_interval_s=0.01, poll_timeout_s=1)
        assert result["status"] == "completed"
        assert result["result"]["text"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_immediately_when_no_answer_id(self):
        api = AsyncMock()
        api.create_answer = AsyncMock(return_value={"text": "immediate"})

        result = await run_answer(api, "test task")
        assert result == {"text": "immediate"}
        api.get_answer.assert_not_called()
