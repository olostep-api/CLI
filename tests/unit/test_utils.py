from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from utils.utils import PollTimeoutError, is_stdout_path, poll, write_json


class TestWriteJson:
    def test_writes_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        data = {"key": "value", "list": [1, 2, 3]}
        write_json(path, data)
        with open(path) as fh:
            loaded = json.load(fh)
        assert loaded == data
        Path(path).unlink()

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nested" / "deep" / "out.json"
            write_json(str(path), {"ok": True})
            assert path.exists()
            assert json.loads(path.read_text()) == {"ok": True}

    def test_unicode_content(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        write_json(path, {"emoji": "🚀", "jp": "日本語"})
        text = Path(path).read_text(encoding="utf-8")
        assert "🚀" in text
        assert "日本語" in text
        Path(path).unlink()

    def test_stdout_writes_json_to_stdout(self, capsys):
        data = {"hello": "world", "n": 42}
        write_json("-", data)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    def test_stdout_no_file_created(self, capsys, tmp_path):
        write_json("-", {"ok": True})
        assert not (tmp_path / "-").exists()


class TestIsStdoutPath:
    def test_dash_is_stdout(self):
        assert is_stdout_path("-") is True

    def test_regular_path_is_not_stdout(self):
        assert is_stdout_path("output/result.json") is False

    def test_path_object_dash(self):
        assert is_stdout_path(Path("-")) is True


class TestPoll:
    @pytest.mark.asyncio
    async def test_returns_immediately_when_done(self):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return {"status": "completed"}

        result = await poll(
            fetch=fetch,
            is_done=lambda obj: obj["status"] == "completed",
            interval_s=0.1,
            timeout_s=5.0,
        )
        assert result == {"status": "completed"}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_polls_until_done(self):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                return {"status": "completed"}
            return {"status": "in_progress"}

        result = await poll(
            fetch=fetch,
            is_done=lambda obj: obj["status"] == "completed",
            interval_s=0.05,
            timeout_s=5.0,
        )
        assert result["status"] == "completed"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_on_tick_called_each_fetch(self):
        call_count = 0
        ticked = []

        async def fetch():
            nonlocal call_count
            call_count += 1
            return {"status": "completed" if call_count >= 3 else "pending", "n": call_count}

        result = await poll(
            fetch=fetch,
            is_done=lambda obj: obj["status"] == "completed",
            interval_s=0.05,
            timeout_s=5.0,
            on_tick=lambda obj: ticked.append(obj),
        )
        assert result["status"] == "completed"
        assert len(ticked) == 3
        assert ticked[-1]["n"] == 3

    @pytest.mark.asyncio
    async def test_on_tick_none_is_fine(self):
        async def fetch():
            return {"status": "done"}

        result = await poll(
            fetch=fetch,
            is_done=lambda obj: obj["status"] == "done",
            interval_s=0.05,
            timeout_s=5.0,
            on_tick=None,
        )
        assert result["status"] == "done"

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        async def fetch():
            return {"status": "in_progress"}

        with pytest.raises(PollTimeoutError, match="Timed out"):
            await poll(
                fetch=fetch,
                is_done=lambda obj: obj["status"] == "completed",
                interval_s=0.05,
                timeout_s=0.15,
            )
