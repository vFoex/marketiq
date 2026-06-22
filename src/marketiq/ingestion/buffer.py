import asyncio
import time
from collections.abc import AsyncIterator

from marketiq.domain.trade import Trade
from marketiq.ingestion.exchange import ExchangeClient
from marketiq.storage.database import session_scope
from marketiq.storage.repository import insert_trades


async def _next_trade(it: AsyncIterator[Trade]) -> Trade:
    """Pull one trade as a coroutine we can schedule as a long-lived Task."""
    return await anext(it)


async def batch_trades(
    trades: AsyncIterator[Trade], batch_size: int, flush_interval: float
) -> AsyncIterator[list[Trade]]:
    it = aiter(trades)
    batch: list[Trade] = []
    deadline = time.monotonic() + flush_interval
    # One outstanding pull, kept alive across flush cycles. We wait on it with a
    # timeout instead of wrapping anext() in wait_for — wait_for would CANCEL the
    # pull on timeout, tearing down the source stream. asyncio.wait does not.
    pending = asyncio.create_task(_next_trade(it))

    try:
        while True:
            timeout = max(deadline - time.monotonic(), 0)
            done, _ = await asyncio.wait({pending}, timeout=timeout)

            if pending not in done:
                # Time's up: flush the partial batch, but leave the pull running.
                if batch:
                    yield batch
                    batch = []
                deadline = time.monotonic() + flush_interval
                continue

            try:
                trade = pending.result()
            except StopAsyncIteration:
                if batch:
                    yield batch
                return

            batch.append(trade)
            pending = asyncio.create_task(_next_trade(it))
            if len(batch) >= batch_size:
                yield batch
                batch = []
                deadline = time.monotonic() + flush_interval
    finally:
        pending.cancel()


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
