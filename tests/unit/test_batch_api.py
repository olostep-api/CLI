from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.batch_api import (
    build_batch_payload,
    collect_results_and_failures,
    normalize_batch_metadata,
    parse_metadata_object,
    parse_retrieve_formats,
    poll_until_completed,
    read_csv_items,
)
from src.batch_scraper import BatchProgress


class TestParseRetrieveFormats:
    def test_single_format(self):
        assert parse_retrieve_formats("markdown") == ["markdown"]

    def test_multiple_formats(self):
        assert parse_retrieve_formats("markdown,html,json") == ["markdown", "html", "json"]

    def test_strips_whitespace(self):
        assert parse_retrieve_formats(" html , markdown ") == ["html", "markdown"]

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="At least one format"):
            parse_retrieve_formats("")

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid format"):
            parse_retrieve_formats("markdown,pdf")


class TestReadCsvItems:
    def _write_csv(self, rows: list[dict], fieldnames: list[str]) -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        )
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        f.close()
        return f.name

    def test_standard_columns(self):
        path = self._write_csv(
            [
                {"custom_id": "item-1", "url": "https://example.com"},
                {"custom_id": "item-2", "url": "https://example.org"},
            ],
            fieldnames=["custom_id", "url"],
        )
        items = read_csv_items(path)
        assert len(items) == 2
        assert items[0] == {"custom_id": "item-1", "url": "https://example.com"}
        Path(path).unlink()

    def test_id_column_fallback(self):
        path = self._write_csv(
            [{"id": "x1", "url": "https://example.com"}],
            fieldnames=["id", "url"],
        )
        items = read_csv_items(path)
        assert items[0]["custom_id"] == "x1"
        Path(path).unlink()

    def test_skips_empty_rows(self):
        path = self._write_csv(
            [
                {"custom_id": "ok", "url": "https://example.com"},
                {"custom_id": "", "url": "https://example.org"},
                {"custom_id": "ok2", "url": ""},
            ],
            fieldnames=["custom_id", "url"],
        )
        items = read_csv_items(path)
        assert len(items) == 1
        Path(path).unlink()

    def test_empty_csv_raises(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        f.write("custom_id,url\n")
        f.close()
        with pytest.raises(ValueError, match="No valid rows"):
            read_csv_items(f.name)
        Path(f.name).unlink()

    def test_no_header_raises(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        f.close()
        with pytest.raises(ValueError):
            read_csv_items(f.name)
        Path(f.name).unlink()


class TestBuildBatchPayload:
    def test_basic_items(self):
        items = [
            {"custom_id": "a", "url": "https://a.com"},
            {"custom_id": "b", "url": "https://b.com"},
        ]
        payload = build_batch_payload(items)
        assert len(payload["items"]) == 2
        assert payload["items"][0] == {"custom_id": "a", "url": "https://a.com"}
        assert "country" not in payload
        assert "parser" not in payload

    def test_with_country_and_parser(self):
        items = [{"custom_id": "x", "url": "https://x.com"}]
        payload = build_batch_payload(items, country="US", parser_id="p1")
        assert payload["country"] == "US"
        assert payload["parser"] == {"id": "p1"}

    def test_omits_empty_optionals(self):
        items = [{"custom_id": "x", "url": "https://x.com"}]
        payload = build_batch_payload(items, country=None, parser_id=None)
        assert "country" not in payload
        assert "parser" not in payload


class TestNormalizeBatchMetadata:
    def test_string_values_passthrough(self):
        assert normalize_batch_metadata({"team": "growth"}) == {"team": "growth"}

    def test_none_becomes_empty_string(self):
        assert normalize_batch_metadata({"tag": None}) == {"tag": ""}

    def test_dict_value_serialized(self):
        result = normalize_batch_metadata({"extra": {"nested": True}})
        assert json.loads(result["extra"]) == {"nested": True}

    def test_list_value_serialized(self):
        result = normalize_batch_metadata({"tags": ["a", "b"]})
        assert json.loads(result["tags"]) == ["a", "b"]

    def test_numeric_value_stringified(self):
        assert normalize_batch_metadata({"count": 42}) == {"count": "42"}

    def test_strips_key_whitespace(self):
        result = normalize_batch_metadata({"  key  ": "val"})
        assert "key" in result

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            normalize_batch_metadata({"": "val"})

    def test_whitespace_only_key_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            normalize_batch_metadata({"   ": "val"})


class TestParseMetadataObject:
    def test_json_string(self):
        result = parse_metadata_object(metadata_json='{"k": "v"}')
        assert result == {"k": "v"}

    def test_json_file(self):
        data = {"file_key": "file_val"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            result = parse_metadata_object(metadata_file=f.name)
        assert result == data
        Path(f.name).unlink()

    def test_both_raises(self):
        with pytest.raises(ValueError, match="only one"):
            parse_metadata_object(metadata_json="{}", metadata_file="f.json")

    def test_neither_raises(self):
        with pytest.raises(ValueError, match="required"):
            parse_metadata_object()

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_metadata_object(metadata_json="not json")

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match="must be a JSON object"):
            parse_metadata_object(metadata_json='"just a string"')


class TestPollUntilCompleted:
    @pytest.mark.asyncio
    async def test_completes_with_progress_bar(self):
        client = AsyncMock()
        client.get_batch_progress = AsyncMock(
            side_effect=[
                BatchProgress(is_completed=False, status="in_progress", total_urls=5, completed_urls=2),
                BatchProgress(is_completed=False, status="in_progress", total_urls=5, completed_urls=4),
                BatchProgress(is_completed=True, status="completed", total_urls=5, completed_urls=5),
            ]
        )
        client.get_batch = AsyncMock(return_value={"id": "b1", "status": "completed"})

        result = await poll_until_completed(
            client, "b1", poll_seconds=0.01, log_every_n_polls=1,
        )
        assert result == {"id": "b1", "status": "completed"}
        assert client.get_batch_progress.call_count == 3

    @pytest.mark.asyncio
    async def test_immediate_completion(self):
        client = AsyncMock()
        client.get_batch_progress = AsyncMock(
            return_value=BatchProgress(is_completed=True, status="completed", total_urls=1, completed_urls=1),
        )
        client.get_batch = AsyncMock(return_value={"id": "b2", "status": "completed"})

        result = await poll_until_completed(
            client, "b2", poll_seconds=0.01, log_every_n_polls=1,
        )
        assert result["status"] == "completed"
        assert client.get_batch_progress.call_count == 1


class TestCollectResultsAndFailures:
    @pytest.mark.asyncio
    async def test_collects_completed_and_failed(self):
        completed_items = [
            {"retrieve_id": "r1", "custom_id": "c1", "url": "https://a.com"},
            {"retrieve_id": "r2", "custom_id": "c2", "url": "https://b.com"},
        ]
        failed_items = [
            {"custom_id": "c3", "url": "https://c.com", "error": "timeout"},
        ]

        client = AsyncMock()

        async def _iter_items(batch_id, *, status, limit):
            items = completed_items if status == "completed" else failed_items
            for item in items:
                yield item

        client.iter_batch_items = _iter_items
        client.retrieve = AsyncMock(return_value={"markdown": "# Hello"})

        results, failures = await collect_results_and_failures(
            client, "b1",
            retrieve_formats=["markdown"],
            items_limit=10,
            expected_completed=2,
        )
        assert len(results) == 2
        assert results[0]["custom_id"] == "c1"
        assert results[0]["retrieved"] == {"markdown": "# Hello"}
        assert len(failures) == 1

    @pytest.mark.asyncio
    async def test_handles_missing_retrieve_id(self):
        client = AsyncMock()

        async def _iter_items(batch_id, *, status, limit):
            if status == "completed":
                yield {"retrieve_id": None, "custom_id": "c1", "url": "https://a.com"}
            # no failed items

        client.iter_batch_items = _iter_items

        results, failures = await collect_results_and_failures(
            client, "b1",
            retrieve_formats=["markdown"],
            items_limit=10,
        )
        assert len(results) == 1
        assert results[0]["error"] == "missing_retrieve_id"
        assert len(failures) == 0
