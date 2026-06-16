from decimal import Decimal

import pytest
from pydantic import ValidationError

from marketiq.domain.trade import Trade
from marketiq.ingestion.binance.normalize import normalize_binance_agg_trade
from marketiq.ingestion.binance.schemas import BinanceAggTrade

RAW = {
    "e": "aggTrade",
    "E": 1672515782136,
    "s": "BTCUSDT",
    "a": 12345,
    "p": "0.001",
    "q": "100",
    "f": 100,
    "l": 105,
    "T": 1672515782136,
    "m": True,
    "M": True,
}


def test_normalize_maps_fields_exactly() -> None:
    trade: Trade = normalize_binance_agg_trade(BinanceAggTrade(**RAW))
    assert trade.id == 12345
    assert trade.symbol == "BTCUSDT"
    assert trade.price == Decimal("0.001")
    assert trade.quantity == Decimal("100")
    assert round(trade.timestamp.timestamp() * 1000) == 1672515782136
    assert trade.timestamp.tzinfo is not None
    assert trade.is_buyer_maker is True


def test_trade_is_immutable() -> None:
    trade: Trade = normalize_binance_agg_trade(BinanceAggTrade(**RAW))
    with pytest.raises(ValidationError):
        trade.price = Decimal("9")  # type: ignore[misc]
