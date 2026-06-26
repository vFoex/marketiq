import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from marketiq.api.routes_rest import router
from marketiq.config import get_settings
from marketiq.ingestion.binance.client import BinanceClient
from marketiq.ingestion.buffer import run_ingestion
from marketiq.processing.pipeline import run_processing

logger = logging.getLogger(__name__)


def _log_crash(task: asyncio.Task[None]) -> None:
    if not task.cancelled() and (exc := task.exception()):
        logger.error("background task crashed", exc_info=exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client = BinanceClient(settings.binance_ws_url, settings.binance_rest_url)
    tasks = [
        asyncio.create_task(
            run_ingestion(
                client,
                settings.symbols,
                settings.batch_size,
                settings.flush_interval_seconds,
            )
        ),
        asyncio.create_task(
            run_processing(
                settings.symbols,
                settings.metrics_window_seconds,
                settings.metrics_interval_seconds,
            )
        ),
    ]
    for t in tasks:
        t.add_done_callback(_log_crash)
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def create_app(*, start_workers: bool = True) -> FastAPI:

    app = FastAPI(lifespan=lifespan if start_workers else None)

    app.include_router(router)
    return app
