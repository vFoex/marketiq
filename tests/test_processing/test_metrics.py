from datetime import UTC, datetime
from decimal import Decimal

from marketiq.domain.trade import Trade
from marketiq.processing.metrics import vwap


def _trade(price: str, quantity: str) -> Trade:
    return Trade(
        id=1,
        symbol="BTCUSDT",
        price=Decimal(price),
        quantity=Decimal(quantity),
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        is_buyer_maker=True,
    )


def test_vwap_two_trades() -> None:
    trades = [
        _trade("100.0", "2.0"),
        _trade("101.0", "3.0"),
    ]
    result = vwap(trades)
    assert result == Decimal("100.6")


def test_vwap_single_trade() -> None:
    trades = [
        _trade("100.0", "2.0"),
    ]
    result = vwap(trades)
    assert result == Decimal("100.0")


def test_vwap_zero_quantity() -> None:
    trades = [
        _trade("100.0", "0.0"),
        _trade("101.0", "0.0"),
    ]
    result = vwap(trades)
    assert result is None


def test_vwap_precision() -> None:
    # Reuse the same precision style trick from storage tests

    trades = [
        _trade("100.000000010000000001", "2.0"),
        _trade("101.000000010000000001", "3.0"),
    ]

    result = vwap(trades)

    assert result == Decimal("100.600000010000000001")
