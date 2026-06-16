from collections.abc import AsyncIterator
from typing import Protocol

from marketiq.domain.trade import Trade


class ExchangeClient(Protocol):
    def stream_trades(self, symbols: list[str]) -> AsyncIterator[Trade]: ...
    async def fetch_recent_trades(self, symbol: str, limit: int) -> list[Trade]: ...
