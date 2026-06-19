from collections.abc import AsyncIterator

import httpx
import websockets

from marketiq.domain.trade import Trade
from marketiq.ingestion.binance.normalize import (
    _event_to_trade,
    normalize_binance_agg_trade,
)
from marketiq.ingestion.binance.schemas import BinanceAggTrade
from marketiq.ingestion.exchange import ExchangeClient


class BinanceClient(ExchangeClient):
    def __init__(self, ws_url: str, rest_url: str):
        self.ws_url = ws_url
        self.rest_url = rest_url

    async def stream_trades(self, symbols: list[str]) -> AsyncIterator[Trade]:
        stream_names = [f"{symbol.lower()}@aggTrade" for symbol in symbols]
        url = f"{self.ws_url}/stream?streams={'/'.join(stream_names)}"
        async for ws in websockets.connect(url):
            try:
                async for raw in ws:
                    yield _event_to_trade(raw)
            except websockets.ConnectionClosed:
                continue

    async def fetch_recent_trades(self, symbol: str, limit: int) -> list[Trade]:
        async with httpx.AsyncClient(base_url=self.rest_url, timeout=10) as client:
            resp = await client.get(
                "/aggTrades", params={"symbol": symbol, "limit": limit}
            )
            resp.raise_for_status()
            rows = resp.json()
            return [
                normalize_binance_agg_trade(BinanceAggTrade(s=symbol, **row))
                for row in rows
            ]
