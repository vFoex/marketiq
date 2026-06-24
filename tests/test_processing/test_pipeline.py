from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.processing.pipeline import process_once, process_window
from marketiq.storage.models import AnomalyRow, MetricRow
from marketiq.storage.repository import insert_trades

# When the cycle ran — deliberately *different* from any trade timestamp, so a
# test can tell whether detected_at came from the clock (wrong) or the data (right).
COMPUTED_AT = datetime(2026, 1, 1, 12, 5, 0, tzinfo=UTC)


def _trade(price: str, *, seconds: int, quantity: str = "1.0") -> Trade:
    return Trade(
        id=seconds,
        symbol="BTCUSDT",
        price=Decimal(price),
        quantity=Decimal(quantity),
        timestamp=datetime(2026, 1, 1, 12, 0, seconds, tzinfo=UTC),
        is_buyer_maker=True,
    )


def test_process_window_empty_returns_none_and_no_events() -> None:
    snapshot, events = process_window("BTCUSDT", [], 60, COMPUTED_AT)

    assert snapshot is None
    assert events == []


def test_process_window_calm_has_snapshot_but_no_events() -> None:
    trades = [
        _trade("100.0", seconds=1),
        _trade("100.5", seconds=2),
        _trade("99.5", seconds=3),
        _trade("100.0", seconds=4),
    ]

    snapshot, events = process_window("BTCUSDT", trades, 60, COMPUTED_AT)

    assert snapshot is not None
    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.computed_at == COMPUTED_AT  # injected clock, not derived
    assert snapshot.window_seconds == 60
    assert snapshot.volume == Decimal("4.0")
    assert snapshot.ohlcv is not None
    assert events == []


def test_process_window_price_spike_produces_event() -> None:
    # flat-ish baseline then a large jump → a price spike, no volume spike
    trades = [
        _trade("100.0", seconds=1),
        _trade("100.1", seconds=2),
        _trade("99.9", seconds=3),
        _trade("100.0", seconds=4),
        _trade("130.0", seconds=5),
    ]

    snapshot, events = process_window("BTCUSDT", trades, 60, COMPUTED_AT)

    assert snapshot is not None
    assert len(events) == 1
    event = events[0]
    assert event.symbol == "BTCUSDT"
    assert event.anomaly.kind == "price_spike"
    # detected_at is the latest TRADE timestamp (12:00:05), NOT computed_at (12:05).
    assert event.detected_at == datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)


def test_process_window_detected_at_uses_latest_trade_not_list_order() -> None:
    # Newest-first list (as the repository returns): detected_at must still be the
    # max timestamp, proving it's derived by time, not by list position.
    trades = [
        _trade("130.0", seconds=5),
        _trade("100.0", seconds=1),
        _trade("100.1", seconds=2),
        _trade("99.9", seconds=3),
        _trade("100.0", seconds=4),
    ]

    _, events = process_window("BTCUSDT", trades, 60, COMPUTED_AT)

    assert events[0].detected_at == datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)


async def test_process_once_persists_metric_and_anomaly(session: AsyncSession) -> None:
    # A spike-tripping window: flat-ish baseline then a jump at 12:00:05.
    trades = [
        _trade("100.0", seconds=1),
        _trade("100.1", seconds=2),
        _trade("99.9", seconds=3),
        _trade("100.0", seconds=4),
        _trade("130.0", seconds=5),
    ]
    await insert_trades(session, trades)
    await session.commit()

    # now is after the trades; window (120s) reaches back before the earliest.
    now = datetime(2026, 1, 1, 12, 1, 0, tzinfo=UTC)
    await process_once(session, "BTCUSDT", window_seconds=120, now=now)
    await session.commit()

    metrics = (await session.execute(select(MetricRow))).scalars().all()
    anomalies = (await session.execute(select(AnomalyRow))).scalars().all()

    assert len(metrics) == 1
    assert metrics[0].computed_at == now
    assert len(anomalies) == 1
    assert anomalies[0].kind == "price_spike"
    # detected_at is the triggering trade's time, not `now`.
    assert anomalies[0].detected_at == datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)
