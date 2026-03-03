from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from config.config import DEFAULT_SCRAPE_FORMATS, SCRAPE_FORMATS_ALLOWED
from src.api_client import OlostepAPI

_ALLOWED_SCRAPE_FORMATS = set(SCRAPE_FORMATS_ALLOWED)


def parse_scrape_formats(formats: str = DEFAULT_SCRAPE_FORMATS) -> List[str]:
    values = [f.strip().lower() for f in formats.split(",") if f.strip()]
    if not values:
        raise ValueError(
            "At least one format is required. Allowed: html, markdown, text, json, raw_pdf, screenshot."
        )
    invalid = [f for f in values if f not in _ALLOWED_SCRAPE_FORMATS]
    if invalid:
        raise ValueError(
            "Invalid scrape format(s): "
            + ", ".join(invalid)
            + ". Allowed: html, markdown, text, json, raw_pdf, screenshot."
        )
    return values


def _parse_json_object(raw: str, source_hint: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {source_hint}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{source_hint} must be a JSON object.")
    return parsed


def load_payload_object(
    payload_json: Optional[str] = None,
    payload_file: Optional[str] = None,
) -> Dict[str, Any]:
    if payload_json is not None and payload_file is not None:
        raise ValueError("Use only one of --payload-json or --payload-file.")

    if payload_json is not None:
        return _parse_json_object(payload_json, "--payload-json")

    if payload_file:
        path = Path(payload_file)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read payload file {payload_file}: {exc}") from exc
        return _parse_json_object(text, "--payload-file")

    return {}


def build_scrape_payload(
    *,
    url_to_scrape: str,
    formats: Optional[List[str]] = None,
    country: Optional[str] = None,
    wait_before_scraping: Optional[int] = None,
    payload_object: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = dict(payload_object or {})
    payload["url_to_scrape"] = url_to_scrape
    if formats is not None:
        payload["formats"] = formats
    if country:
        payload["country"] = country
    if wait_before_scraping is not None:
        payload["wait_before_scraping"] = wait_before_scraping
    return payload


async def run_scrape(
    api: OlostepAPI,
    *,
    url_to_scrape: str,
    formats: List[str],
    country: Optional[str] = None,
    wait_before_scraping: Optional[int] = None,
    payload_object: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = build_scrape_payload(
        url_to_scrape=url_to_scrape,
        formats=formats,
        country=country,
        wait_before_scraping=wait_before_scraping,
        payload_object=payload_object,
    )
    logger.info("Creating scrape...")
    return await api.create_scrape(payload)


async def run_scrape_get(api: OlostepAPI, scrape_id: str) -> Dict[str, Any]:
    logger.info(f"Fetching scrape: {scrape_id}")
    return await api.get_scrape(scrape_id)
