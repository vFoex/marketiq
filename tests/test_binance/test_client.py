import json
from decimal import Decimal

import httpx
import pytest
import respx

from marketiq.ingestion.binance.client import BinanceClient
from marketiq.ingestion.binance.normalize import _event_to_trade

# A single aggTrade payload, as Binance sends it on the wire.
AGG_TRADE = {
    "a": 12345,
    "s": "BTCUSDT",
    "p": "0.001",
    "q": "100",
    "T": 1672515782136,
    "m": True,
}

REST_URL = "https://api.binance.test"


def test_event_to_trade_unwraps_combined_stream_envelope() -> None:
    # Combined-stream messages wrap the event under "data"; the parser must peel it.
    raw = json.dumps({"stream": "btcusdt@aggTrade", "data": AGG_TRADE})

    trade = _event_to_trade(raw)

    assert trade.id == 12345
    assert trade.symbol == "BTCUSDT"
    assert trade.price == Decimal("0.001")


def test_event_to_trade_bare_event() -> None:
    raw = json.dumps(AGG_TRADE)

    trade = _event_to_trade(raw)

    assert trade.id == 12345
    assert trade.symbol == "BTCUSDT"
    assert trade.price == Decimal("0.001")


@respx.mock
async def test_fetch_recent_trades_injects_symbol() -> None:
    # REST /aggTrades rows have NO "s" field — the client must supply the symbol.
    rest_row = {k: v for k, v in AGG_TRADE.items() if k != "s"}
    route = respx.get(f"{REST_URL}/aggTrades").mock(
        return_value=httpx.Response(200, json=[rest_row])
    )

    client = BinanceClient(
        ws_url="wss://stream.binance.test",
        rest_url=REST_URL,
    )
    trades = await client.fetch_recent_trades("BTCUSDT", limit=1)

    assert route.called
    assert len(trades) == 1
    assert trades[0].symbol == "BTCUSDT"  # proved: the client injected it
    assert trades[0].price == Decimal("0.001")


@respx.mock
async def test_fetch_recent_trades_error_path() -> None:
    route = respx.get(f"{REST_URL}/aggTrades").mock(
        return_value=httpx.Response(500, json={"code": -1000, "msg": "Internal error"})
    )

    client = BinanceClient(
        ws_url="wss://stream.binance.test",
        rest_url=REST_URL,
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.fetch_recent_trades("BTCUSDT", limit=1)

    assert route.called
