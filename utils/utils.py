from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, TypeVar

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from config.config import DEFAULT_ANSWER_POLL_INTERVAL_S, DEFAULT_ANSWER_POLL_TIMEOUT_S

T = TypeVar("T")

STDOUT_MARKER = "-"

console = Console(stderr=True)


def is_stdout_path(path: str | Path) -> bool:
    return str(path) == STDOUT_MARKER


def ensure_parent_dir(path: str | Path) -> None:
    p = Path(path)
    if p.parent and str(p.parent) not in ("", "."):
        p.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: str | Path, data: Any) -> None:
    if is_stdout_path(path):
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        sys.stdout.flush()
        return
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class PollTimeoutError(TimeoutError):
    pass


def make_progress(**kwargs: Any) -> Progress:
    defaults = dict(
        transient=True,
        console=console,
    )
    defaults.update(kwargs)
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        **defaults,
    )


async def poll(
    fetch: Callable[[], Awaitable[T]],
    is_done: Callable[[T], bool],
    *,
    interval_s: float = DEFAULT_ANSWER_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_ANSWER_POLL_TIMEOUT_S,
    on_tick: Optional[Callable[[T], None]] = None,
) -> T:
    start = time.time()
    while True:
        obj = await fetch()
        if on_tick is not None:
            on_tick(obj)
        if is_done(obj):
            return obj
        if time.time() - start > timeout_s:
            raise PollTimeoutError(f"Timed out after {timeout_s}s")
        await asyncio.sleep(interval_s)
