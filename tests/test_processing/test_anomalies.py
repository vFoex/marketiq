from datetime import UTC, datetime
from decimal import Decimal

from marketiq.domain.trade import Trade
from marketiq.processing.anomalies import price_spike, volume_spike


def _trade(price: str, *, seconds: int, quantity: str = "1.0") -> Trade:
    return Trade(
        id=seconds,
        symbol="BTCUSDT",
        price=Decimal(price),
        quantity=Decimal(quantity),
        timestamp=datetime(2026, 1, 1, 12, 0, seconds, tzinfo=UTC),
        is_buyer_maker=True,
    )


def test_anomalies_exact_treshold_spike() -> None:
    trades = [
        _trade("10.0", seconds=1),
        _trade("14.0", seconds=2),
        _trade("18.0", seconds=3),
    ]

    anomaly = price_spike(trades)

    assert anomaly is not None
    assert anomaly.kind == "price_spike"
    assert anomaly.z_score == Decimal("3.0")
    assert anomaly.value == Decimal("18.0")


def test_anomalies_below_treshold_no_spike() -> None:
    trades = [
        _trade("10.0", seconds=1),
        _trade("14.0", seconds=2),
        _trade("17.0", seconds=3),
    ]

    anomaly = price_spike(trades)

    assert anomaly is None


def test_anomalies_downward_spike() -> None:
    trades = [
        _trade("10.0", seconds=1),
        _trade("14.0", seconds=2),
        _trade("6.0", seconds=3),
    ]

    anomaly = price_spike(trades)

    assert anomaly is not None
    assert anomaly.kind == "price_spike"
    assert anomaly.z_score == Decimal("-3.0")
    assert "below" in anomaly.reason


def test_anomalies_sigma_equal_to_zero_and_jump() -> None:
    trades = [
        _trade("100.0", seconds=1),
        _trade("100.0", seconds=2),
        _trade("105.0", seconds=3),
    ]

    anomaly = price_spike(trades)

    assert anomaly is not None
    assert anomaly.kind == "price_spike"
    assert anomaly.z_score is None
    assert "∞" in anomaly.reason


def test_anomalies_sigma_equal_to_zero_and_no_move() -> None:
    trades = [
        _trade("100.0", seconds=1),
        _trade("100.0", seconds=2),
        _trade("100.0", seconds=3),
    ]

    anomaly = price_spike(trades)

    assert anomaly is None


def test_anomalies_not_enough_data() -> None:
    no_trades: list[Trade] = []

    trades = [
        _trade("100.0", seconds=1),
    ]

    anomaly_none = price_spike(no_trades)
    anomaly_single = price_spike(trades)

    assert anomaly_none is None
    assert anomaly_single is None


def test_anomalies_sort_out_of_order() -> None:
    trades = [
        _trade("18.0", seconds=3),
        _trade("14.0", seconds=2),
        _trade("10.0", seconds=1),
    ]

    anomaly = price_spike(trades)

    assert anomaly is not None
    assert anomaly.kind == "price_spike"
    assert anomaly.z_score == Decimal("3.0")
    assert anomaly.value == Decimal("18.0")


def test_anomalies_volume_spike() -> None:
    trades = [
        _trade("10.0", seconds=1, quantity="10.0"),
        _trade("10.0", seconds=2, quantity="14.0"),
        _trade("10.0", seconds=3, quantity="18.0"),
    ]

    anomaly = volume_spike(trades)

    assert anomaly is not None
    assert anomaly.kind == "volume_spike"
    assert anomaly.z_score == Decimal("3.0")
