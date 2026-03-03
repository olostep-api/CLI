from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

from config.config import DEFAULT_HTTP_TIMEOUT_S


class OlostepAPIError(RuntimeError):
    pass


@dataclass
class OlostepAPI:
    api_key: str
    base_url: str
    timeout_s: float = DEFAULT_HTTP_TIMEOUT_S

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=httpx.Timeout(self.timeout_s),
        )

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise OlostepAPIError(f"HTTP {resp.status_code}: {body}")

    async def create_map(
        self,
        url: str,
        *,
        search_query: Optional[str] = None,
        top_n: Optional[int] = None,
        include_subdomain: Optional[bool] = None,
        include_urls: Optional[Sequence[str]] = None,
        exclude_urls: Optional[Sequence[str]] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": url}
        if search_query:
            payload["search_query"] = search_query
        if top_n is not None:
            payload["top_n"] = top_n
        if include_subdomain is not None:
            payload["include_subdomain"] = include_subdomain
        if include_urls:
            payload["include_urls"] = list(include_urls)
        if exclude_urls:
            payload["exclude_urls"] = list(exclude_urls)
        if cursor:
            payload["cursor"] = cursor

        async with self._client() as c:
            r = await c.post("/maps", json=payload)
            self._raise_for_status(r)
            return r.json()

    async def create_answer(
        self,
        task: str,
        *,
        json_format: Optional[Any] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"task": task}
        if json_format is not None:
            payload["json_format"] = json_format

        async with self._client() as c:
            r = await c.post("/answers", json=payload)
            self._raise_for_status(r)
            return r.json()

    async def get_answer(self, answer_id: str) -> Dict[str, Any]:
        async with self._client() as c:
            r = await c.get(f"/answers/{answer_id}")
            self._raise_for_status(r)
            return r.json()

    async def create_scrape(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self._client() as c:
            r = await c.post("/scrapes", json=payload)
            self._raise_for_status(r)
            return r.json()

    async def get_scrape(self, scrape_id: str) -> Dict[str, Any]:
        async with self._client() as c:
            r = await c.get(f"/scrapes/{scrape_id}")
            self._raise_for_status(r)
            return r.json()

    async def create_crawl(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self._client() as c:
            r = await c.post("/crawls", json=payload)
            self._raise_for_status(r)
            return r.json()

    async def get_crawl(self, crawl_id: str) -> Dict[str, Any]:
        async with self._client() as c:
            r = await c.get(f"/crawls/{crawl_id}")
            self._raise_for_status(r)
            return r.json()

    async def list_crawl_pages(
        self,
        crawl_id: str,
        *,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if search_query:
            params["search_query"] = search_query

        async with self._client() as c:
            r = await c.get(f"/crawls/{crawl_id}/pages", params=params)
            self._raise_for_status(r)
            return r.json()

    async def retrieve_content(
        self,
        retrieve_id: str,
        *,
        formats: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        params: List[Tuple[str, str]] = [("retrieve_id", retrieve_id)]
        if formats:
            for fmt in formats:
                params.append(("formats", str(fmt)))
        async with self._client() as c:
            r = await c.get("/retrieve", params=params)
            self._raise_for_status(r)
            return r.json()
