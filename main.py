from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, List, Optional

import typer
from loguru import logger

from config.config import (
    DEFAULT_ANSWER_OUT_PATH,
    DEFAULT_ANSWER_POLL_INTERVAL_S,
    DEFAULT_ANSWER_POLL_TIMEOUT_S,
    DEFAULT_BATCH_FORMATS,
    DEFAULT_BATCH_ITEMS_LIMIT,
    DEFAULT_BATCH_LOG_EVERY,
    DEFAULT_BATCH_OUT_PATH,
    DEFAULT_BATCH_POLL_SECONDS,
    DEFAULT_BATCH_UPDATE_OUT_PATH,
    DEFAULT_CRAWL_FORMATS,
    DEFAULT_CRAWL_MAX_PAGES,
    DEFAULT_CRAWL_OUT_PATH,
    DEFAULT_CRAWL_PAGES_LIMIT,
    DEFAULT_CRAWL_POLL_SECONDS,
    DEFAULT_CRAWL_POLL_TIMEOUT_S,
    DEFAULT_HTTP_TIMEOUT_S,
    DEFAULT_MAP_OUT_PATH,
    DEFAULT_SCRAPE_FORMATS,
    DEFAULT_SCRAPE_GET_OUT_PATH,
    DEFAULT_SCRAPE_OUT_PATH,
    Settings,
    resolve_api_key,
)
from src.answer_api import run_answer
from src.api_client import OlostepAPI
from src.batch_api import parse_retrieve_formats, run_batch_scrape, run_batch_update
from src.crawl_api import parse_crawl_retrieve_formats, run_crawl
from src.map_api import run_map
from src.scrape_api import parse_scrape_formats, run_scrape, run_scrape_get
from utils.utils import write_json

app = typer.Typer(
    add_completion=False,
    help="Olostep CLI: map, answer, scrape, scrape-get, crawl, batch-scrape, batch-update",
)


def _make_api(timeout_s: float) -> OlostepAPI:
    s = Settings.from_env(timeout_s=timeout_s)
    return OlostepAPI(api_key=s.api_key, base_url=s.base_url, timeout_s=s.timeout_s)


def _get_token() -> str:
    return resolve_api_key()


def _parse_json_format(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        raise typer.BadParameter("--json-format cannot be empty", param_hint="--json-format")
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return raw


def _load_json_object_input(
    *,
    raw_json: Optional[str],
    file_path: Optional[str],
    json_flag: str,
    file_flag: str,
) -> Optional[dict[str, Any]]:
    if raw_json is not None and file_path is not None:
        raise typer.BadParameter(
            f"Use only one of {json_flag} or {file_flag}.",
            param_hint=f"{json_flag}/{file_flag}",
        )

    if raw_json is None and file_path is None:
        return None

    source_hint = json_flag
    text = raw_json
    if file_path is not None:
        source_hint = file_flag
        try:
            text = Path(file_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise typer.BadParameter(
                f"Cannot read {file_flag} file {file_path}: {exc}",
                param_hint=file_flag,
            ) from exc

    try:
        parsed = json.loads(text or "")
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(
            f"Invalid JSON for {source_hint}: {exc}",
            param_hint=source_hint,
        ) from exc

    if not isinstance(parsed, dict):
        raise typer.BadParameter(
            f"{source_hint} must be a JSON object.",
            param_hint=source_hint,
        )
    return parsed


@app.command("crawl")
def crawl_cmd(
    start_url: str = typer.Argument(..., help="Start URL for crawl"),
    out: str = typer.Option(DEFAULT_CRAWL_OUT_PATH, "--out", help="Output JSON path"),
    max_pages: int = typer.Option(
        DEFAULT_CRAWL_MAX_PAGES, "--max-pages", help="Maximum pages to crawl"
    ),
    max_depth: Optional[int] = typer.Option(
        None, "--max-depth", help="Optional maximum crawl depth"
    ),
    include_subdomain: Optional[bool] = typer.Option(
        None,
        "--include-subdomain/--no-include-subdomain",
        help="Include subdomain URLs while crawling",
    ),
    include_external: Optional[bool] = typer.Option(
        None,
        "--include-external/--no-include-external",
        help="Include external domain URLs while crawling",
    ),
    include_urls: Optional[List[str]] = typer.Option(
        None, "--include-url", help="Include only these URL patterns (repeatable)"
    ),
    exclude_urls: Optional[List[str]] = typer.Option(
        None, "--exclude-url", help="Exclude these URL patterns (repeatable)"
    ),
    search_query: Optional[str] = typer.Option(
        None, "--search-query", help="Optional search query for crawl discovery"
    ),
    top_n: Optional[int] = typer.Option(
        None, "--top-n", help="Optional cap on returned pages relevant to search query"
    ),
    webhook: Optional[str] = typer.Option(None, "--webhook", help="Optional webhook URL"),
    crawl_timeout: Optional[int] = typer.Option(
        None, "--crawl-timeout", help="Optional crawl timeout in seconds"
    ),
    follow_robots_txt: bool = typer.Option(
        True,
        "--follow-robots-txt/--ignore-robots-txt",
        help="Respect robots.txt rules",
    ),
    formats: str = typer.Option(
        DEFAULT_CRAWL_FORMATS,
        "--formats",
        help='Comma-separated retrieve formats: "markdown,html,json"',
    ),
    pages_limit: int = typer.Option(
        DEFAULT_CRAWL_PAGES_LIMIT, "--pages-limit", help="Pages API page size (cursor pagination)"
    ),
    pages_search_query: Optional[str] = typer.Option(
        None, "--pages-search-query", help="Filter query for crawl pages listing"
    ),
    poll_seconds: float = typer.Option(
        DEFAULT_CRAWL_POLL_SECONDS, "--poll-seconds", help="Crawl status polling interval seconds"
    ),
    poll_timeout: float = typer.Option(
        DEFAULT_CRAWL_POLL_TIMEOUT_S, "--poll-timeout", help="Crawl polling timeout seconds"
    ),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    if max_pages < 1:
        raise typer.BadParameter("--max-pages must be >= 1", param_hint="--max-pages")
    if max_depth is not None and max_depth < 0:
        raise typer.BadParameter("--max-depth must be >= 0", param_hint="--max-depth")
    if top_n is not None and top_n < 1:
        raise typer.BadParameter("--top-n must be >= 1", param_hint="--top-n")
    if crawl_timeout is not None and crawl_timeout < 1:
        raise typer.BadParameter("--crawl-timeout must be >= 1", param_hint="--crawl-timeout")
    if pages_limit < 1:
        raise typer.BadParameter("--pages-limit must be >= 1", param_hint="--pages-limit")
    if poll_seconds <= 0:
        raise typer.BadParameter("--poll-seconds must be > 0", param_hint="--poll-seconds")
    if poll_timeout <= 0:
        raise typer.BadParameter("--poll-timeout must be > 0", param_hint="--poll-timeout")

    try:
        retrieve_formats = parse_crawl_retrieve_formats(formats)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--formats") from exc

    api = _make_api(timeout_s)
    result = asyncio.run(
        run_crawl(
            api,
            start_url=start_url,
            max_pages=max_pages,
            retrieve_formats=retrieve_formats,
            max_depth=max_depth,
            include_subdomain=include_subdomain,
            include_external=include_external,
            include_urls=include_urls,
            exclude_urls=exclude_urls,
            search_query=search_query,
            top_n=top_n,
            webhook=webhook,
            timeout=crawl_timeout,
            follow_robots_txt=follow_robots_txt,
            poll_seconds=poll_seconds,
            poll_timeout_s=poll_timeout,
            pages_limit=pages_limit,
            pages_search_query=pages_search_query,
        )
    )
    write_json(out, result)
    logger.info(f"Wrote: {out}")


@app.command("map")
def map_cmd(
    url: str = typer.Argument(..., help="Website URL to map"),
    out: str = typer.Option(DEFAULT_MAP_OUT_PATH, "--out", help="Output JSON path"),
    include_subdomain: Optional[bool] = typer.Option(
        None,
        "--include-subdomain/--no-include-subdomain",
        help="Include subdomain URLs in map results",
    ),
    top_n: Optional[int] = typer.Option(None, "--top-n", help="Maximum URLs to return"),
    search_query: Optional[str] = typer.Option(
        None, "--search-query", help="Optional search query to guide URL discovery"
    ),
    include_urls: Optional[List[str]] = typer.Option(
        None, "--include-url", help="Include only these URL patterns (repeatable)"
    ),
    exclude_urls: Optional[List[str]] = typer.Option(
        None, "--exclude-url", help="Exclude these URL patterns (repeatable)"
    ),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="Pagination cursor for maps API"),
    legacy_limit: Optional[int] = typer.Option(None, "--limit", hidden=True),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    if legacy_limit is not None:
        raise typer.BadParameter("`--limit` was removed. Use `--top-n`.", param_hint="--limit")
    if top_n is not None and top_n < 1:
        raise typer.BadParameter("--top-n must be >= 1", param_hint="--top-n")

    api = _make_api(timeout_s)
    result = asyncio.run(
        run_map(
            api,
            url,
            search_query=search_query,
            top_n=top_n,
            include_subdomain=include_subdomain,
            include_urls=include_urls,
            exclude_urls=exclude_urls,
            cursor=cursor,
        )
    )
    write_json(out, result)
    logger.info(f"Wrote: {out}")


@app.command("answer")
def answer_cmd(
    task: str = typer.Argument(..., help="Task/question for Olostep Answers"),
    out: str = typer.Option(DEFAULT_ANSWER_OUT_PATH, "--out", help="Output JSON path"),
    json_format: Optional[str] = typer.Option(
        None,
        "--json-format",
        help='Optional JSON format/schema (example: \'{"company":"","year":""}\')',
    ),
    legacy_model: Optional[str] = typer.Option(None, "--model", hidden=True),
    poll_interval: float = typer.Option(
        DEFAULT_ANSWER_POLL_INTERVAL_S, "--poll-interval", help="Polling interval seconds"
    ),
    poll_timeout: float = typer.Option(
        DEFAULT_ANSWER_POLL_TIMEOUT_S, "--poll-timeout", help="Polling timeout seconds"
    ),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    if legacy_model is not None:
        raise typer.BadParameter(
            "`--model` was removed. Use `--json-format`.", param_hint="--model"
        )

    parsed_json_format = _parse_json_format(json_format)
    api = _make_api(timeout_s)
    result = asyncio.run(
        run_answer(
            api,
            task,
            json_format=parsed_json_format,
            poll_interval_s=poll_interval,
            poll_timeout_s=poll_timeout,
        )
    )
    write_json(out, result)
    logger.info(f"Wrote: {out}")


@app.command("scrape")
def scrape_cmd(
    url_to_scrape: str = typer.Argument(..., help="URL to scrape"),
    out: str = typer.Option(DEFAULT_SCRAPE_OUT_PATH, "--out", help="Output JSON path"),
    formats: str = typer.Option(
        DEFAULT_SCRAPE_FORMATS,
        "--formats",
        help='Comma-separated formats: "html,markdown,text,json,raw_pdf,screenshot"',
    ),
    country: Optional[str] = typer.Option(None, "--country", help="Optional country code"),
    wait_before_scraping: Optional[int] = typer.Option(
        None,
        "--wait-before-scraping",
        help="Optional wait time before scraping (milliseconds)",
    ),
    payload_json: Optional[str] = typer.Option(
        None,
        "--payload-json",
        help="Optional advanced scrape payload as JSON object string",
    ),
    payload_file: Optional[str] = typer.Option(
        None,
        "--payload-file",
        help="Optional path to a JSON file containing advanced scrape payload object",
    ),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    if wait_before_scraping is not None and wait_before_scraping < 0:
        raise typer.BadParameter(
            "--wait-before-scraping must be >= 0",
            param_hint="--wait-before-scraping",
        )

    try:
        scrape_formats = parse_scrape_formats(formats)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--formats") from exc

    payload_object = _load_json_object_input(
        raw_json=payload_json,
        file_path=payload_file,
        json_flag="--payload-json",
        file_flag="--payload-file",
    )

    api = _make_api(timeout_s)
    result = asyncio.run(
        run_scrape(
            api,
            url_to_scrape=url_to_scrape,
            formats=scrape_formats,
            country=country,
            wait_before_scraping=wait_before_scraping,
            payload_object=payload_object,
        )
    )
    write_json(out, result)
    logger.info(f"Wrote: {out}")


@app.command("scrape-get")
def scrape_get_cmd(
    scrape_id: str = typer.Argument(..., help="Scrape ID"),
    out: str = typer.Option(DEFAULT_SCRAPE_GET_OUT_PATH, "--out", help="Output JSON path"),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    api = _make_api(timeout_s)
    result = asyncio.run(run_scrape_get(api, scrape_id))
    write_json(out, result)
    logger.info(f"Wrote: {out}")


@app.command("batch-scrape")
def batch_scrape_cmd(
    csv_path: str = typer.Argument(..., help="CSV with columns: custom_id,url (or id,url)"),
    out: str = typer.Option(DEFAULT_BATCH_OUT_PATH, "--out", help="Output JSON path"),
    formats: str = typer.Option(
        DEFAULT_BATCH_FORMATS,
        "--formats",
        help='Comma-separated formats: "markdown,html,json"',
    ),
    country: Optional[str] = typer.Option(
        None, "--country", help="Optional country code (e.g. US, GB, PK)"
    ),
    parser_id: Optional[str] = typer.Option(
        None, "--parser-id", help="Optional parser id for structured extraction"
    ),
    poll_seconds: float = typer.Option(
        DEFAULT_BATCH_POLL_SECONDS, "--poll-seconds", help="Polling interval seconds"
    ),
    log_every: int = typer.Option(DEFAULT_BATCH_LOG_EVERY, "--log-every", help="Log every N polls"),
    items_limit: int = typer.Option(
        DEFAULT_BATCH_ITEMS_LIMIT,
        "--items-limit",
        help="Batch items page size (API recommends 10-50)",
    ),
):
    try:
        retrieve_formats = parse_retrieve_formats(formats)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--formats") from exc

    if poll_seconds <= 0:
        raise typer.BadParameter("--poll-seconds must be > 0", param_hint="--poll-seconds")
    if log_every < 1:
        raise typer.BadParameter("--log-every must be >= 1", param_hint="--log-every")
    if items_limit < 1:
        raise typer.BadParameter("--items-limit must be >= 1", param_hint="--items-limit")

    tok = _get_token()
    result = asyncio.run(
        run_batch_scrape(
            csv_path=csv_path,
            output_json_path=out,
            api_token=tok,
            country=country,
            parser_id=parser_id,
            poll_seconds=poll_seconds,
            retrieve_formats=retrieve_formats,
            log_every_n_polls=log_every,
            items_limit=items_limit,
        )
    )
    logger.info(
        "Batch complete: id={} completed={} failed={}",
        result.get("batch_id"),
        result.get("results_count"),
        result.get("failed_count"),
    )


@app.command("batch-update")
def batch_update_cmd(
    batch_id: str = typer.Argument(..., help="Batch ID"),
    metadata_json: Optional[str] = typer.Option(
        None,
        "--metadata-json",
        help="Batch metadata JSON object string",
    ),
    metadata_file: Optional[str] = typer.Option(
        None,
        "--metadata-file",
        help="Path to JSON file containing batch metadata object",
    ),
    out: str = typer.Option(
        DEFAULT_BATCH_UPDATE_OUT_PATH,
        "--out",
        help="Output JSON path",
    ),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    metadata_obj = _load_json_object_input(
        raw_json=metadata_json,
        file_path=metadata_file,
        json_flag="--metadata-json",
        file_flag="--metadata-file",
    )
    if metadata_obj is None:
        raise typer.BadParameter(
            "One of --metadata-json or --metadata-file is required.",
            param_hint="--metadata-json/--metadata-file",
        )

    tok = _get_token()
    result = asyncio.run(
        run_batch_update(
            batch_id=batch_id,
            output_json_path=out,
            api_token=tok,
            metadata=metadata_obj,
            timeout=timeout_s,
        )
    )
    logger.info("Batch updated: id={}", result.get("id", batch_id))


if __name__ == "__main__":
    app()
