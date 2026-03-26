from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from config.config import DEFAULT_ANSWER_POLL_INTERVAL_S, DEFAULT_ANSWER_POLL_TIMEOUT_S
from src.api_client import OlostepAPI
from utils.utils import console, poll


_SUCCESS_STATUSES = {"completed", "succeeded", "done", "finished", "success"}
_FAILED_STATUSES = {"failed", "error", "cancelled", "canceled"}


def _is_done(answer_obj: Dict[str, Any]) -> bool:
    status = (answer_obj.get("status") or "").lower()
    if not status:
        logger.warning("Answer response has no 'status' field; continuing to poll")
        return False
    return status in _SUCCESS_STATUSES or status in _FAILED_STATUSES


async def run_answer(
    api: OlostepAPI,
    task: str,
    *,
    json_format: Optional[Any] = None,
    poll_interval_s: float = DEFAULT_ANSWER_POLL_INTERVAL_S,
    poll_timeout_s: float = DEFAULT_ANSWER_POLL_TIMEOUT_S,
) -> Dict[str, Any]:
    logger.info("Creating answer...")
    created = await api.create_answer(task=task, json_format=json_format)

    answer_id = created.get("answer_id") or created.get("id") or created.get("answerId")
    if not answer_id:
        return created

    logger.info(f"Answer created: {answer_id}")
    with console.status(f"[bold blue]Waiting for answer {answer_id}…"):
        final = await poll(
            fetch=lambda: api.get_answer(str(answer_id)),
            is_done=_is_done,
            interval_s=poll_interval_s,
            timeout_s=poll_timeout_s,
        )

    status = (final.get("status") or "").lower()
    if status in _FAILED_STATUSES:
        raise RuntimeError(
            f"Answer {answer_id} finished with status={status}: {final}"
        )
    return final
