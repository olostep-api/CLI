from __future__ import annotations

import asyncio
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, cast

from loguru import logger

from config.config import (
    BATCH_RETRIEVE_PROGRESS_LOG_EVERY,
    DEFAULT_BATCH_LOG_EVERY,
    DEFAULT_BATCH_ITEMS_LIMIT,
    DEFAULT_BATCH_POLL_SECONDS,
    DEFAULT_HTTP_TIMEOUT_S,
    DEFAULT_RETRIEVE_FORMATS,
    RETRIEVE_FORMATS_ALLOWED,
)
from src.batch_scraper import BatchScraper
from utils.utils import write_json

RetrieveFormat = Literal["html", "markdown", "json"]
_ALLOWED_FORMATS = set(RETRIEVE_FORMATS_ALLOWED)


def _ts() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def parse_retrieve_formats(formats: str) -> List[RetrieveFormat]:
    values = [f.strip().lower() for f in formats.split(",") if f.strip()]
    if not values:
        raise ValueError("At least one format is required. Allowed: markdown, html, json.")
    invalid = [f for f in values if f not in _ALLOWED_FORMATS]
    if invalid:
        raise ValueError(
            f"Invalid format(s): {', '.join(invalid)}. Allowed: markdown, html, json."
        )
    return [cast(RetrieveFormat, f) for f in values]


def read_csv_items(csv_path: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(
                "CSV has no header row. Expected columns: custom_id,url (or id,url)"
            )

        for row in reader:
            rid = (row.get("custom_id") or row.get("id") or "").strip()
            url = (row.get("url") or "").strip()
            if not rid or not url:
                continue
            items.append({"custom_id": rid, "url": url})

    if not items:
        raise ValueError(
            "No valid rows found. Ensure CSV has non-empty 'custom_id' (or 'id') and 'url' columns."
        )
    return items


def _parse_json_object(raw: str, source_hint: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {source_hint}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{source_hint} must be a JSON object.")
    return parsed


def parse_metadata_object(
    metadata_json: Optional[str] = None,
    metadata_file: Optional[str] = None,
) -> Dict[str, Any]:
    if metadata_json is not None and metadata_file is not None:
        raise ValueError("Use only one of --metadata-json or --metadata-file.")
    if metadata_json is not None:
        return _parse_json_object(metadata_json, "--metadata-json")
    if metadata_file:
        path = Path(metadata_file)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read metadata file {metadata_file}: {exc}") from exc
        return _parse_json_object(text, "--metadata-file")
    raise ValueError("One of --metadata-json or --metadata-file is required.")


def normalize_batch_metadata(raw_metadata: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in raw_metadata.items():
        if not isinstance(key, str):
            raise ValueError("Metadata keys must be strings.")
        k = key.strip()
        if not k:
            raise ValueError("Metadata keys must be non-empty strings.")
        if value is None:
            normalized[k] = ""
            continue
        if isinstance(value, str):
            normalized[k] = value
            continue
        if isinstance(value, (dict, list)):
            normalized[k] = json.dumps(value, ensure_ascii=False)
            continue
        normalized[k] = str(value)
    return normalized


async def poll_until_completed(
    client: BatchScraper,
    batch_id: str,
    *,
    poll_seconds: float,
    log_every_n_polls: int,
) -> Dict[str, Any]:
    poll_i = 0
    start = time.time()
    last_completed: Optional[int] = None
    last_total: Optional[int] = None

    while True:
        poll_i += 1
        progress = await client.get_batch_progress(batch_id)

        should_log = poll_i % max(1, log_every_n_polls) == 0
        changed = (progress.completed_urls != last_completed) or (
            progress.total_urls != last_total
        )
        if should_log or changed or progress.is_completed:
            elapsed = int(time.time() - start)
            logger.info(
                f"[{_ts()}] Batch {batch_id} status={progress.status} "
                f"progress={progress.completed_urls}/{progress.total_urls} "
                f"elapsed={elapsed}s"
            )
            last_completed = progress.completed_urls
            last_total = progress.total_urls

        if progress.is_completed:
            break

        await asyncio.sleep(poll_seconds)

    return await client.get_batch(batch_id)


async def collect_results_and_failures(
    client: BatchScraper,
    batch_id: str,
    *,
    retrieve_formats: List[RetrieveFormat],
    items_limit: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    results: List[Dict[str, Any]] = []
    completed_count = 0
    size_exceeded_count = 0
    first_size_exceeded_ids: List[str] = []

    async for item in client.iter_batch_items(
        batch_id, status="completed", limit=items_limit
    ):
        completed_count += 1
        retrieve_id = item.get("retrieve_id")
        custom_id = item.get("custom_id")
        url = item.get("url")

        if not retrieve_id:
            results.append(
                {"custom_id": custom_id, "url": url, "error": "missing_retrieve_id"}
            )
            continue

        if completed_count % BATCH_RETRIEVE_PROGRESS_LOG_EVERY == 0:
            logger.info(
                f"[{_ts()}] Retrieving content... {completed_count} completed items processed"
            )

        retrieved = await client.retrieve(retrieve_id, formats=retrieve_formats)
        if isinstance(retrieved, dict) and retrieved.get("size_exceeded") is True:
            size_exceeded_count += 1
            if custom_id and len(first_size_exceeded_ids) < 3:
                first_size_exceeded_ids.append(str(custom_id))

        results.append(
            {
                "custom_id": custom_id,
                "url": url,
                "retrieve_id": retrieve_id,
                "retrieved": retrieved,
            }
        )

    if size_exceeded_count:
        id_hint = ""
        if first_size_exceeded_ids:
            id_hint = (
                f" (first affected custom_id(s): {', '.join(first_size_exceeded_ids)})"
            )
        logger.warning(
            f"[{_ts()}] Note: {size_exceeded_count} item(s) had size_exceeded=true{id_hint}. "
            "Their content may be in *_hosted_url fields (hosted URLs expire after ~7 days)."
        )

    failed_items: List[Dict[str, Any]] = []
    async for item in client.iter_batch_items(batch_id, status="failed", limit=items_limit):
        failed_items.append(item)

    return results, failed_items


async def run_batch_scrape(
    csv_path: str,
    output_json_path: str,
    api_token: str,
    *,
    country: Optional[str] = None,
    parser_id: Optional[str] = None,
    poll_seconds: float = DEFAULT_BATCH_POLL_SECONDS,
    retrieve_formats: Optional[List[RetrieveFormat]] = None,
    log_every_n_polls: int = DEFAULT_BATCH_LOG_EVERY,
    items_limit: int = DEFAULT_BATCH_ITEMS_LIMIT,
) -> Dict[str, Any]:
    if poll_seconds <= 0:
        raise ValueError("--poll-seconds must be > 0")
    if log_every_n_polls < 1:
        raise ValueError("--log-every must be >= 1")
    if items_limit < 1:
        raise ValueError("--items-limit must be >= 1")

    if retrieve_formats is None:
        retrieve_formats = [cast(RetrieveFormat, f) for f in DEFAULT_RETRIEVE_FORMATS]

    items = read_csv_items(csv_path)

    async with BatchScraper(api_token=api_token) as client:
        batch_resp = await client.create_batch(items, country=country, parser_id=parser_id)
        batch_id = batch_resp.get("id")
        if not batch_id:
            raise RuntimeError(f"Batch create response missing 'id': {batch_resp}")

        logger.info(f"[{_ts()}] Created batch: {batch_id} (urls={len(items)})")

        final_batch = await poll_until_completed(
            client,
            batch_id,
            poll_seconds=poll_seconds,
            log_every_n_polls=log_every_n_polls,
        )

        results, failed_items = await collect_results_and_failures(
            client,
            batch_id,
            retrieve_formats=retrieve_formats,
            items_limit=items_limit,
        )

        logger.info(
            f"[{_ts()}] Items: completed={len(results)} failed={len(failed_items)} total={len(items)}"
        )

        payload: Dict[str, Any] = {
            "batch": final_batch,
            "batch_id": batch_id,
            "requested_count": len(items),
            "results_count": len(results),
            "results": results,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
        }
        write_json(output_json_path, payload)
        logger.info(f"[{_ts()}] Saved: {output_json_path} (results={len(results)})")
        return payload


async def run_batch_update(
    *,
    batch_id: str,
    output_json_path: str,
    api_token: str,
    metadata: Optional[Dict[str, Any]] = None,
    metadata_json: Optional[str] = None,
    metadata_file: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT_S,
) -> Dict[str, Any]:
    raw_metadata = metadata
    if raw_metadata is None:
        raw_metadata = parse_metadata_object(metadata_json=metadata_json, metadata_file=metadata_file)

    normalized = normalize_batch_metadata(raw_metadata)
    if not normalized:
        raise ValueError("Metadata cannot be empty.")

    async with BatchScraper(api_token=api_token, base_url=base_url, timeout=timeout) as client:
        updated = await client.update_batch(batch_id=batch_id, metadata=normalized)
        write_json(output_json_path, updated)
        logger.info(f"[{_ts()}] Saved: {output_json_path}")
        return updated
