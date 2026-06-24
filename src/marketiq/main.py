import asyncio
import logging
import sys

from marketiq.config import get_settings
from marketiq.ingestion.binance.client import BinanceClient
from marketiq.ingestion.buffer import run_ingestion
from marketiq.processing.pipeline import run_processing


async def run() -> None:
    settings = get_settings()
    client = BinanceClient(settings.binance_ws_url, settings.binance_rest_url)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(
            run_ingestion(
                client,
                settings.symbols,
                settings.batch_size,
                settings.flush_interval_seconds,
            )
        )
        tg.create_task(
            run_processing(
                settings.symbols,
                settings.metrics_window_seconds,
                settings.metrics_interval_seconds,
            )
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
