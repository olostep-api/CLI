from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from loguru import logger

from config.config import (
    DEFAULT_CRAWL_FORMATS,
    DEFAULT_CRAWL_PAGES_LIMIT,
    DEFAULT_CRAWL_POLL_SECONDS,
    DEFAULT_CRAWL_POLL_TIMEOUT_S,
    RETRIEVE_FORMATS_ALLOWED,
)
from src.api_client import OlostepAPI
from utils.utils import poll

_ALLOWED_RETRIEVE_FORMATS = set(RETRIEVE_FORMATS_ALLOWED)


def parse_crawl_retrieve_formats(formats: str = DEFAULT_CRAWL_FORMATS) -> List[str]:
    values = [v.strip().lower() for v in formats.split(",") if v.strip()]
    if not values:
        raise ValueError("At least one format is required. Allowed: markdown, html, json.")
    invalid = [v for v in values if v not in _ALLOWED_RETRIEVE_FORMATS]
    if invalid:
        raise ValueError(
            f"Invalid format(s): {', '.join(invalid)}. Allowed: markdown, html, json."
        )
    return values


def build_crawl_payload(
    *,
    start_url: str,
    max_pages: int,
    max_depth: Optional[int] = None,
    include_subdomain: Optional[bool] = None,
    include_external: Optional[bool] = None,
    include_urls: Optional[Sequence[str]] = None,
    exclude_urls: Optional[Sequence[str]] = None,
    search_query: Optional[str] = None,
    top_n: Optional[int] = None,
    webhook: Optional[str] = None,
    timeout: Optional[int] = None,
    follow_robots_txt: Optional[bool] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "start_url": start_url,
        "max_pages": max_pages,
    }
    if max_depth is not None:
        payload["max_depth"] = max_depth
    if include_subdomain is not None:
        payload["include_subdomain"] = include_subdomain
    if include_external is not None:
        payload["include_external"] = include_external
    if include_urls:
        payload["include_urls"] = list(include_urls)
    if exclude_urls:
        payload["exclude_urls"] = list(exclude_urls)
    if search_query:
        payload["search_query"] = search_query
    if top_n is not None:
        payload["top_n"] = top_n
    if webhook:
        payload["webhook"] = webhook
    if timeout is not None:
        payload["timeout"] = timeout
    if follow_robots_txt is not None:
        payload["follow_robots_txt"] = follow_robots_txt
    return payload


def _crawl_status(crawl_obj: Dict[str, Any]) -> str:
    return str(crawl_obj.get("status") or "").lower()


def _is_crawl_terminal(crawl_obj: Dict[str, Any]) -> bool:
    return _crawl_status(crawl_obj) in {"completed", "failed", "cancelled", "canceled", "error"}


async def _collect_crawl_results(
    api: OlostepAPI,
    crawl_id: str,
    *,
    retrieve_formats: Sequence[str],
    pages_limit: int = DEFAULT_CRAWL_PAGES_LIMIT,
    pages_search_query: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    cursor: Optional[int] = None
    rows: List[Dict[str, Any]] = []
    missing_retrieve_id = 0

    while True:
        page = await api.list_crawl_pages(
            crawl_id,
            cursor=cursor,
            limit=pages_limit,
            search_query=pages_search_query,
        )
        pages = page.get("pages", []) or []
        for p in pages:
            retrieve_id = p.get("retrieve_id")
            if not retrieve_id:
                missing_retrieve_id += 1
                rows.append({"page": p, "error": "missing_retrieve_id"})
                continue
            retrieved = await api.retrieve_content(str(retrieve_id), formats=retrieve_formats)
            rows.append({"page": p, "retrieved": retrieved})

        next_cursor = page.get("cursor")
        if next_cursor is None:
            break
        cursor = int(next_cursor)

    return rows, missing_retrieve_id


async def run_crawl(
    api: OlostepAPI,
    *,
    start_url: str,
    max_pages: int,
    retrieve_formats: Sequence[str],
    max_depth: Optional[int] = None,
    include_subdomain: Optional[bool] = None,
    include_external: Optional[bool] = None,
    include_urls: Optional[Sequence[str]] = None,
    exclude_urls: Optional[Sequence[str]] = None,
    search_query: Optional[str] = None,
    top_n: Optional[int] = None,
    webhook: Optional[str] = None,
    timeout: Optional[int] = None,
    follow_robots_txt: Optional[bool] = None,
    poll_seconds: float = DEFAULT_CRAWL_POLL_SECONDS,
    poll_timeout_s: float = DEFAULT_CRAWL_POLL_TIMEOUT_S,
    pages_limit: int = DEFAULT_CRAWL_PAGES_LIMIT,
    pages_search_query: Optional[str] = None,
) -> Dict[str, Any]:
    payload = build_crawl_payload(
        start_url=start_url,
        max_pages=max_pages,
        max_depth=max_depth,
        include_subdomain=include_subdomain,
        include_external=include_external,
        include_urls=include_urls,
        exclude_urls=exclude_urls,
        search_query=search_query,
        top_n=top_n,
        webhook=webhook,
        timeout=timeout,
        follow_robots_txt=follow_robots_txt,
    )
    logger.info("Creating crawl...")
    created = await api.create_crawl(payload)
    crawl_id = created.get("id") or created.get("crawl_id")
    if not crawl_id:
        raise RuntimeError(f"Crawl create response missing id: {created}")
    crawl_id = str(crawl_id)

    logger.info(f"Crawl created: {crawl_id}. Polling...")
    final_crawl = await poll(
        fetch=lambda: api.get_crawl(crawl_id),
        is_done=_is_crawl_terminal,
        interval_s=poll_seconds,
        timeout_s=poll_timeout_s,
    )
    status = _crawl_status(final_crawl)
    if status != "completed":
        raise RuntimeError(f"Crawl {crawl_id} finished with status={status}: {final_crawl}")

    results, missing_retrieve_id = await _collect_crawl_results(
        api,
        crawl_id,
        retrieve_formats=retrieve_formats,
        pages_limit=pages_limit,
        pages_search_query=pages_search_query,
    )

    return {
        "crawl_id": crawl_id,
        "crawl": final_crawl,
        "crawl_create": created,
        "results_count": len(results),
        "missing_retrieve_id_count": missing_retrieve_id,
        "results": results,
    }
