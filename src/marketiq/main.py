import asyncio
import sys

from marketiq.config import get_settings
from marketiq.ingestion.binance.client import BinanceClient
from marketiq.ingestion.buffer import run_ingestion


async def run() -> None:
    settings = get_settings()
    client = BinanceClient(settings.binance_ws_url, settings.binance_rest_url)
    await run_ingestion(
        client, settings.symbols, settings.batch_size, settings.flush_interval_seconds
    )


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
