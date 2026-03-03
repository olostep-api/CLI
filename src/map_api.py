from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from loguru import logger

from src.api_client import OlostepAPI


async def run_map(
    api: OlostepAPI,
    url: str,
    *,
    search_query: Optional[str] = None,
    top_n: Optional[int] = None,
    include_subdomain: Optional[bool] = None,
    include_urls: Optional[Sequence[str]] = None,
    exclude_urls: Optional[Sequence[str]] = None,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    logger.info(f"Mapping: {url}")
    return await api.create_map(
        url,
        search_query=search_query,
        top_n=top_n,
        include_subdomain=include_subdomain,
        include_urls=include_urls,
        exclude_urls=exclude_urls,
        cursor=cursor,
    )
