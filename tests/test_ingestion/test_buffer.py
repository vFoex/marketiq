import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

from marketiq.domain.trade import Trade
from marketiq.ingestion.buffer import batch_trades


def _trade(trade_id: int) -> Trade:
    return Trade(
        id=trade_id,
        symbol="BTCUSDT",
        price=Decimal("100.00"),
        quantity=Decimal("1"),
        timestamp=datetime(2026, 1, 1, 12, 0, trade_id, tzinfo=UTC),
        is_buyer_maker=True,
    )


async def _stream(trades: list[Trade]) -> AsyncIterator[Trade]:
    """Wrap a list as an async stream that ends after the last item."""
    for trade in trades:
        yield trade


async def test_batches_by_size_and_flushes_remainder() -> None:
    # 5 trades, batch_size=2 → [2, 2, 1]: the last partial batch must still flush.
    trades = [_trade(i) for i in range(5)]
    batches = [
        batch
        async for batch in batch_trades(
            _stream(trades), batch_size=2, flush_interval=60
        )
    ]
    assert [len(batch) for batch in batches] == [2, 2, 1]


async def test_exact_fill_leaves_no_empty_tail() -> None:
    # 4 trades, batch_size=2 → [2, 2]: no trailing empty batch on stream end.
    trades = [_trade(i) for i in range(4)]
    batches = [
        batch
        async for batch in batch_trades(
            _stream(trades), batch_size=2, flush_interval=60
        )
    ]
    assert [len(batch) for batch in batches] == [2, 2]


async def test_time_flush_keeps_stream_alive() -> None:
    # trade 0 arrives, then the stream idles past flush_interval → trade 0 is
    # flushed alone on the timeout. Crucially the stream must SURVIVE that flush
    # and still deliver trade 1 as a second batch — the old wait_for(anext) code
    # cancelled the in-flight pull on timeout and killed the stream here.
    async def slow_stream() -> AsyncIterator[Trade]:
        yield _trade(0)
        await asyncio.sleep(0.05)  # longer than flush_interval below
        yield _trade(1)

    # batch_size=10 guarantees only the timeout — not a full batch — flushed each.
    agen = batch_trades(slow_stream(), batch_size=10, flush_interval=0.01)
    first = await anext(agen)  # flushed by the timeout
    second = await anext(agen)  # only arrives if the stream outlived the timeout

    assert [t.id for t in first] == [0]
    assert [t.id for t in second] == [1]
