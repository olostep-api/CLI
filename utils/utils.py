from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

from config.config import DEFAULT_ANSWER_POLL_INTERVAL_S, DEFAULT_ANSWER_POLL_TIMEOUT_S

T = TypeVar("T")


def ensure_parent_dir(path: str | Path) -> None:
    p = Path(path)
    if p.parent and str(p.parent) not in ("", "."):
        p.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: str | Path, data: Any) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class PollTimeoutError(TimeoutError):
    pass


async def poll(
    fetch: Callable[[], Awaitable[T]],
    is_done: Callable[[T], bool],
    *,
    interval_s: float = DEFAULT_ANSWER_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_ANSWER_POLL_TIMEOUT_S,
) -> T:
    start = time.time()
    while True:
        obj = await fetch()
        if is_done(obj):
            return obj
        if time.time() - start > timeout_s:
            raise PollTimeoutError(f"Timed out after {timeout_s}s")
        await asyncio.sleep(interval_s)
