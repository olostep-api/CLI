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
    get_cli_auth_api_base,
    get_cli_auth_page_url,
    get_credentials_path,
    load_env_file,
    resolve_api_key,
)
from src.answer_api import run_answer
from src.api_client import OlostepAPI
from src.cli_auth import (
    CliAuthError,
    merge_env_api_key,
    run_browser_login,
    save_credentials_json,
)
from src.batch_api import build_batch_payload, parse_retrieve_formats, read_csv_items, run_batch_scrape, run_batch_update
from src.crawl_api import build_crawl_payload, parse_crawl_retrieve_formats, run_crawl
from src.map_api import run_map
from src.scrape_api import parse_scrape_formats, run_scrape, run_scrape_get
from src.skills_install import (
    CLI_LOCAL_SKILLS_DIR,
    DEFAULT_CANONICAL_DIR,
    DEFAULT_LOCKFILE,
    InstallOptions,
    RemoveOptions,
    run_install as run_skills_install,
    run_remove as run_skills_remove,
)
from utils.utils import is_stdout_path, write_json

app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="Olostep CLI: login, map, answer, scrape, scrape-get, crawl, batch-scrape, batch-update",
)
add_app = typer.Typer(help="Add resources to local agent environments.")
app.add_typer(add_app, name="add")
remove_app = typer.Typer(help="Remove resources from local agent environments.")
app.add_typer(remove_app, name="remove")

__version__ = "0.1.0"


def _version_callback(value: bool) -> None:
    if value:
        print(f"olostep {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Olostep CLI"""


def _make_api(timeout_s: float) -> OlostepAPI:
    s = Settings.from_env(timeout_s=timeout_s)
    return OlostepAPI(api_key=s.api_key, base_url=s.base_url, timeout_s=s.timeout_s)


def _get_token() -> str:
    return resolve_api_key()


@app.command("login")
def login_cmd(
    poll_seconds: float = typer.Option(
        3.0,
        "--poll-seconds",
        help="Interval between POST /status polls",
    ),
    timeout_s: float = typer.Option(
        600.0,
        "--timeout",
        help="Give up after this many seconds waiting for authorization",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Print the authorize URL instead of opening a browser",
    ),
    env_file: Optional[str] = typer.Option(
        None,
        "--env-file",
        help="Write API key to this .env file instead of the default credentials.json",
    ),
):
    """Sign in via browser and save the API key (default: OS config dir credentials.json).

    Opens the Olostep CLI authorize page; after you click Authorize, the CLI polls until your key is ready.
    """
    _run_login_flow(
        poll_seconds=poll_seconds,
        timeout_s=timeout_s,
        no_browser=no_browser,
        env_file=env_file,
    )


@add_app.command("skills")
def add_skills_cmd(
    login: bool = typer.Option(False, "--login", help="Run `olostep login` flow before installing skills."),
    source: str = typer.Option(str(CLI_LOCAL_SKILLS_DIR), "--source", help="Skills source directory (default: CLI bundled skills)."),
    cli_local_dir: str = typer.Option(str(CLI_LOCAL_SKILLS_DIR), "--cli-local-dir", help="CLI-local skills copy destination."),
    agent: Optional[List[str]] = typer.Option(None, "--agent", help="Install for this agent only (repeatable)."),
    all_agents: bool = typer.Option(True, "--all-agents/--no-all-agents", help="Install for all detected agents."),
    global_install: bool = typer.Option(True, "--global/--no-global", help="Install into global agent skills directories."),
    canonical_dir: str = typer.Option(str(DEFAULT_CANONICAL_DIR), "--canonical-dir", help="Canonical skills directory."),
    agent_skills_dir: Optional[str] = typer.Option(None, "--agent-skills-dir", help="Override target skills directory (non-global mode)."),
    skill: Optional[List[str]] = typer.Option(None, "--skill", help="Only install these skill names (repeatable)."),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", help="Exclude these skill names (repeatable)."),
    overwrite: bool = typer.Option(True, "--overwrite/--no-overwrite", help="Replace existing installed skills."),
    link_mode: str = typer.Option("auto", "--link-mode", help="Agent install mode: auto, symlink, copy."),
    as_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON output."),
):
    """Add Olostep skills from local plugin into agent skill directories."""
    if link_mode not in {"auto", "symlink", "copy"}:
        raise typer.BadParameter("--link-mode must be one of: auto, symlink, copy", param_hint="--link-mode")
    if agent_skills_dir and global_install:
        raise typer.BadParameter("--agent-skills-dir requires --no-global", param_hint="--agent-skills-dir")
    if not global_install and not agent_skills_dir:
        raise typer.BadParameter("Use --agent-skills-dir when running with --no-global", param_hint="--agent-skills-dir")

    if login:
        _run_login_flow(
            poll_seconds=3.0,
            timeout_s=600.0,
            no_browser=False,
            env_file=None,
        )

    options = InstallOptions(
        source=Path(source).expanduser(),
        cli_local_dir=Path(cli_local_dir).expanduser(),
        canonical_dir=Path(canonical_dir).expanduser(),
        lockfile_path=DEFAULT_LOCKFILE,
        agent=agent or [],
        all_agents=all_agents,
        global_install=global_install,
        agent_skills_dir=Path(agent_skills_dir).expanduser() if agent_skills_dir else None,
        skill=skill or [],
        exclude=exclude or [],
        dry_run=False,
        overwrite=overwrite,
        link_mode=link_mode,  # type: ignore[arg-type]
        yes=True,
    )
    try:
        result = run_skills_install(options)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except OSError as exc:
        raise typer.BadParameter(f"File operation failed: {exc}") from exc

    if as_json:
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    typer.secho("")
    typer.secho("  ✓  Skills installation finished.", fg="green", bold=True)
    typer.secho(f"  Source: {result['sync']['plugin_source_dir']}", dim=True)
    typer.secho(f"  CLI local copy: {result['sync']['cli_local_dir']}", dim=True)
    typer.secho(f"  Canonical dir: {result['canonical_dir']}", dim=True)
    typer.secho(f"  Installed skills: {', '.join(result['selected_skills'])}", dim=True)
    if result["targets"]:
        typer.secho(f"  Targets: {', '.join(result['targets'])}", dim=True)
    else:
        typer.secho("  Targets: none", dim=True)
    typer.secho("")


@remove_app.command("skills")
def remove_skills_cmd(
    agent: Optional[List[str]] = typer.Option(None, "--agent", help="Remove from this agent only (repeatable)."),
    all_agents: bool = typer.Option(True, "--all-agents/--no-all-agents", help="Remove from all detected agents."),
    canonical_dir: str = typer.Option(str(DEFAULT_CANONICAL_DIR), "--canonical-dir", help="Canonical skills directory."),
    agent_skills_dir: Optional[str] = typer.Option(None, "--agent-skills-dir", help="Override target skills directory."),
    skill: Optional[List[str]] = typer.Option(None, "--skill", help="Only remove these skill names (repeatable)."),
    as_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON output."),
):
    """Remove installed Olostep skills from canonical and agent directories."""
    options = RemoveOptions(
        canonical_dir=Path(canonical_dir).expanduser(),
        lockfile_path=DEFAULT_LOCKFILE,
        agent=agent or [],
        all_agents=all_agents,
        agent_skills_dir=Path(agent_skills_dir).expanduser() if agent_skills_dir else None,
        skill=skill or [],
        dry_run=False,
        yes=True,
    )
    try:
        result = run_skills_remove(options)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except OSError as exc:
        raise typer.BadParameter(f"File operation failed: {exc}") from exc

    if as_json:
        print(json.dumps(result, indent=2, default=str))
        raise typer.Exit()

    typer.secho("")
    typer.secho("  ✓  Skills removal finished.", fg="green", bold=True)
    typer.secho(f"  Canonical removed: {', '.join(result['removed_canonical']) or 'none'}", dim=True)
    typer.secho(f"  Target entries removed: {len(result['removed_targets'])}", dim=True)
    typer.secho("")


def _run_login_flow(
    *,
    poll_seconds: float,
    timeout_s: float,
    no_browser: bool,
    env_file: Optional[str],
) -> None:
    load_env_file()
    try:
        resolved_api = get_cli_auth_api_base()
        resolved_page = get_cli_auth_page_url()
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if poll_seconds <= 0:
        raise typer.BadParameter("--poll-seconds must be > 0", param_hint="--poll-seconds")
    if timeout_s <= 0:
        raise typer.BadParameter("--timeout must be > 0", param_hint="--timeout")

    try:
        api_key = run_browser_login(
            api_base=resolved_api,
            page_url=resolved_page,
            poll_seconds=poll_seconds,
            timeout_s=timeout_s,
            no_browser=no_browser,
        )
        if env_file:
            env_path = Path(env_file).expanduser()
            merge_env_api_key(env_path, api_key)
            out_desc: Path | str = env_path
        else:
            cred_path = get_credentials_path()
            save_credentials_json(cred_path, api_key)
            out_desc = cred_path
    except CliAuthError as exc:
        typer.secho(f"\n  ✗  {exc}\n", fg="red", err=True)
        logger.error(str(exc))
        raise typer.Exit(code=1) from exc

    tail = api_key[-4:] if len(api_key) >= 4 else "****"
    typer.secho("")
    typer.secho("  ✓  Signed in successfully.", fg="green", bold=True)
    typer.secho(f"  Credentials saved to {out_desc}", dim=True)
    typer.secho(f"  Key ends with …{tail}", dim=True)
    typer.secho("")
    logger.debug("Login saved API key to {} (suffix …{})", out_desc, tail)


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
    out: str = typer.Option(DEFAULT_CRAWL_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
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
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the API payload as JSON and exit without sending it"
    ),
):
    """Crawl a website starting from a URL and retrieve page contents.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep crawl "https://docs.example.com" --max-pages 50

    [dim]$[/dim] olostep crawl "https://example.com" --max-pages 20 --max-depth 2 --formats markdown,html

    [dim]$[/dim] olostep crawl "https://example.com" --max-pages 100 --search-query "pricing" --top-n 10

    [dim]$[/dim] olostep crawl "https://example.com" --max-pages 10 --dry-run
    """
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

    if dry_run:
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
            timeout=crawl_timeout,
            follow_robots_txt=follow_robots_txt,
        )
        payload["_retrieve_formats"] = list(retrieve_formats)
        print(json.dumps(payload, indent=2))
        raise typer.Exit()

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
    if not is_stdout_path(out):
        logger.info(f"Wrote: {out}")


@app.command("map")
def map_cmd(
    url: str = typer.Argument(..., help="Website URL to map"),
    out: str = typer.Option(DEFAULT_MAP_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
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
    """Discover all URLs on a website.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep map "https://example.com"

    [dim]$[/dim] olostep map "https://example.com" --top-n 100 --search-query "blog"

    [dim]$[/dim] olostep map "https://example.com" --include-subdomain --out - | jq '.urls[:5]'
    """
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
    if not is_stdout_path(out):
        logger.info(f"Wrote: {out}")


@app.command("answer")
def answer_cmd(
    task: str = typer.Argument(..., help="Task/question for Olostep Answers"),
    out: str = typer.Option(DEFAULT_ANSWER_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
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
    """Ask a question and get a researched answer from the web.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep answer "What is Olostep and what are its main features?"

    [dim]$[/dim] olostep answer "Who is the CEO of OpenAI?" --out - | jq .result

    [dim]$[/dim] olostep answer "Top 3 Python web frameworks" --json-format '{"frameworks": [{"name": "", "url": ""}]}'
    """
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
    if not is_stdout_path(out):
        logger.info(f"Wrote: {out}")


@app.command("scrape")
def scrape_cmd(
    url_to_scrape: str = typer.Argument(..., help="URL to scrape"),
    out: str = typer.Option(DEFAULT_SCRAPE_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
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
    """Scrape a single URL and return its content in one or more formats.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep scrape "https://example.com"

    [dim]$[/dim] olostep scrape "https://example.com" --formats markdown,html --country US

    [dim]$[/dim] olostep scrape "https://example.com" --payload-json '{"remove_selectors": [".nav", ".footer"]}'

    [dim]$[/dim] olostep scrape "https://example.com" --out - | jq .result.markdown_content
    """
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
    if not is_stdout_path(out):
        logger.info(f"Wrote: {out}")


@app.command("scrape-get")
def scrape_get_cmd(
    scrape_id: str = typer.Argument(..., help="Scrape ID"),
    out: str = typer.Option(DEFAULT_SCRAPE_GET_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    """Retrieve the result of a previous scrape by its ID.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep scrape-get scrape_abc123

    [dim]$[/dim] olostep scrape-get scrape_abc123 --out - | jq .result.markdown_content
    """
    api = _make_api(timeout_s)
    result = asyncio.run(run_scrape_get(api, scrape_id))
    write_json(out, result)
    if not is_stdout_path(out):
        logger.info(f"Wrote: {out}")


@app.command("batch-scrape")
def batch_scrape_cmd(
    csv_path: str = typer.Argument(..., help="CSV with columns: custom_id,url (or id,url)"),
    out: str = typer.Option(DEFAULT_BATCH_OUT_PATH, "--out", help="Output JSON path (use '-' for stdout)"),
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
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the API payload as JSON and exit without sending it"
    ),
):
    """Scrape many URLs in parallel from a CSV file.

    The CSV must have columns [bold]custom_id[/bold] (or [bold]id[/bold]) and [bold]url[/bold].

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep batch-scrape urls.csv

    [dim]$[/dim] olostep batch-scrape urls.csv --formats markdown,html --country US

    [dim]$[/dim] olostep batch-scrape urls.csv --parser-id my-parser --out results.json

    [dim]$[/dim] olostep batch-scrape urls.csv --dry-run
    """
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

    if dry_run:
        items = read_csv_items(csv_path)
        payload = build_batch_payload(items, country=country, parser_id=parser_id)
        payload["_retrieve_formats"] = list(retrieve_formats)
        print(json.dumps(payload, indent=2))
        raise typer.Exit()

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
        help="Output JSON path (use '-' for stdout)",
    ),
    timeout_s: float = typer.Option(
        DEFAULT_HTTP_TIMEOUT_S, "--timeout", help="HTTP timeout in seconds"
    ),
):
    """Update metadata on an existing batch.

    [bold]Examples:[/bold]

    [dim]$[/dim] olostep batch-update batch_abc123 --metadata-json '{"team": "growth", "project": "q1"}'

    [dim]$[/dim] olostep batch-update batch_abc123 --metadata-file meta.json

    [dim]$[/dim] olostep batch-update batch_abc123 --metadata-json '{"status": "reviewed"}' --out -
    """
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
