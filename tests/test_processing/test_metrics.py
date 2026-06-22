from datetime import UTC, datetime
from decimal import Decimal
from math import log, sqrt

import pytest

from marketiq.domain.trade import Trade
from marketiq.processing.metrics import OHLCV, ohlcv, realized_volatility, volume, vwap


def _trade(price: str, quantity: str, *, seconds: int = 0) -> Trade:
    return Trade(
        id=1,
        symbol="BTCUSDT",
        price=Decimal(price),
        quantity=Decimal(quantity),
        timestamp=datetime(2026, 1, 1, 12, 0, seconds, tzinfo=UTC),
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


def test_ohlcv() -> None:
    trades = [
        _trade("99.0", "1.0", seconds=3),  # position 0, LATEST in time
        _trade("100.0", "2.0", seconds=1),  # position 1, EARLIEST in time
        _trade("101.0", "3.0", seconds=2),  # position 2
    ]
    result = ohlcv(trades)
    assert result == OHLCV(
        open=Decimal("100.0"),  # earliest time — and now ≠ trades[0] (99.0)
        high=Decimal("101.0"),
        low=Decimal("99.0"),
        close=Decimal("99.0"),  # latest time — and now ≠ trades[-1] (101.0)
        volume=Decimal("6.0"),
    )


def test_ohlcv_empty() -> None:
    result = ohlcv([])

    assert result is None


def test_volume_sums_quantities() -> None:
    trades = [_trade("100.0", "2.0"), _trade("101.0", "3.0")]
    assert volume(trades) == Decimal("5.0")


def test_volume_precision() -> None:
    # Decimal must sum sub-unit quantities a float would round away.
    trades = [
        _trade("100.0", "0.000000010000000001"),
        _trade("100.0", "0.000000010000000002"),
    ]
    assert volume(trades) == Decimal("0.000000020000000003")


def test_volume_empty_is_zero() -> None:
    # Contrast with vwap: volume of no trades is a real answer (0), not undefined.
    assert volume([]) == Decimal("0")


def test_realized_volatility_constant_price_is_zero() -> None:
    # Every log return is ln(1) = 0, so Σr² = 0 → vol = 0.
    trades = [
        _trade("100.0", "1.0", seconds=1),
        _trade("100.0", "1.0", seconds=2),
        _trade("100.0", "1.0", seconds=3),
    ]
    assert realized_volatility(trades) == Decimal("0")


def test_realized_volatility_known_value() -> None:
    # 100→110→121: two equal returns of ln(1.1) → sqrt(2·ln(1.1)²) = √2·ln(1.1).
    trades = [
        _trade("100.0", "1.0", seconds=1),
        _trade("110.0", "1.0", seconds=2),
        _trade("121.0", "1.0", seconds=3),
    ]
    result = realized_volatility(trades)
    assert result is not None
    # Independent oracle via float math, compared with approx (float vs Decimal).
    assert float(result) == pytest.approx(sqrt(2) * log(1.1))


def test_realized_volatility_sorts_by_time() -> None:
    # List order ≠ time order, and not a mere reversal: without the internal sort
    # the list-adjacent pairs would be non-time-adjacent and the result would differ.
    ordered = [
        _trade("100.0", "1.0", seconds=1),
        _trade("110.0", "1.0", seconds=2),
        _trade("121.0", "1.0", seconds=3),
    ]
    scrambled = [
        _trade("110.0", "1.0", seconds=2),
        _trade("121.0", "1.0", seconds=3),
        _trade("100.0", "1.0", seconds=1),
    ]
    assert realized_volatility(scrambled) == realized_volatility(ordered)


def test_realized_volatility_insufficient_data_is_none() -> None:
    assert realized_volatility([]) is None
    assert realized_volatility([_trade("100.0", "1.0")]) is None
