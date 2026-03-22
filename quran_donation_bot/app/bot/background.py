import asyncio
import logging
from collections.abc import Callable


logger = logging.getLogger(__name__)


def run_db_task(function: Callable[[], None]) -> asyncio.Task:
    async def runner() -> None:
        try:
            await asyncio.to_thread(function)
        except Exception:
            logger.exception("Background database task failed")

    return asyncio.create_task(runner())
