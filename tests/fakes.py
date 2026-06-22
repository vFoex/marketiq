from collections.abc import AsyncIterator

from marketiq.domain.trade import Trade


class FakeExchangeClient:
    """In-memory ExchangeClient for deterministic ingestion tests.

    Structural typing: this satisfies the ExchangeClient Protocol by having the
    right methods — no base class needed. `stream_trades` replays a canned list
    and then completes (the stream "ends"), which is exactly what lets us assert
    the tail-flush behaviour without a real socket.
    """

    def __init__(self, trades: list[Trade]) -> None:
        self._trades = trades

    async def stream_trades(self, symbols: list[str]) -> AsyncIterator[Trade]:
        for trade in self._trades:
            yield trade

    async def fetch_recent_trades(self, symbol: str, limit: int) -> list[Trade]:
        return self._trades[:limit]
