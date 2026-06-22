import asyncio
import time
from collections.abc import AsyncIterator

from marketiq.domain.trade import Trade
from marketiq.ingestion.exchange import ExchangeClient
from marketiq.storage.database import session_scope
from marketiq.storage.repository import insert_trades


async def batch_trades(
    trades: AsyncIterator[Trade], batch_size: int, flush_interval: float
) -> AsyncIterator[list[Trade]]:
    it = aiter(trades)
    batch: list[Trade] = []
    deadline = time.monotonic() + flush_interval

    while True:
        timeout = deadline - time.monotonic()
        try:
            trade = await asyncio.wait_for(anext(it), timeout)
        except TimeoutError:
            if batch:
                yield batch
                batch = []
            deadline = time.monotonic() + flush_interval
            continue
        except StopAsyncIteration:
            if batch:
                yield batch
            return

        batch.append(trade)
        if len(batch) >= batch_size:
            yield batch
            batch = []
            deadline = time.monotonic() + flush_interval


async def run_ingestion(
    client: ExchangeClient,
    symbols: list[str],
    batch_size: int,
    flush_interval: float,
) -> None:
    async for batch in batch_trades(
        client.stream_trades(symbols), batch_size, flush_interval
    ):
        async with session_scope() as session:
            await insert_trades(session, batch)
