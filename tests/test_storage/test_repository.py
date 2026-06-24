from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.processing.anomalies import Anomaly, AnomalyEvent
from marketiq.processing.metrics import OHLCV, MetricSnapshot
from marketiq.storage.mappers import row_to_event, row_to_snapshot
from marketiq.storage.models import AnomalyRow, MetricRow
from marketiq.storage.repository import (
    get_recent_trades,
    get_trades_since,
    insert_anomaly,
    insert_metric,
    insert_trades,
)


def _trade(trade_id: int, price: str) -> Trade:
    return Trade(
        id=trade_id,
        symbol="BTCUSDT",
        price=Decimal(price),
        quantity=Decimal("1.5"),
        # distinct seconds → distinct timestamps, so ordering is deterministic
        timestamp=datetime(2026, 1, 1, 12, 0, trade_id, tzinfo=UTC),
        is_buyer_maker=True,
    )


def _snapshot(
    computed_at: datetime,
    *,
    vwap: Decimal | None,
    volatility: Decimal | None,
    ohlcv: OHLCV | None,
) -> MetricSnapshot:
    return MetricSnapshot(
        symbol="BTCUSDT",
        computed_at=computed_at,
        window_seconds=60,
        vwap=vwap,
        volume=Decimal("6.0"),
        volatility=volatility,
        ohlcv=ohlcv,
    )


def _bar() -> OHLCV:
    return OHLCV(
        open=Decimal("100.0"),
        high=Decimal("110.0"),
        low=Decimal("99.0"),
        close=Decimal("105.0"),
        volume=Decimal("6.0"),
    )


def _event(detected_at: datetime, *, z_score: Decimal | None) -> AnomalyEvent:
    return AnomalyEvent(
        symbol="BTCUSDT",
        detected_at=detected_at,
        anomaly=Anomaly(
            kind="price_spike",
            value=Decimal("130.0"),
            mean=Decimal("100.0"),
            std_dev=Decimal("2.0"),
            z_score=z_score,
            reason="price 130 is 15.00σ above mean 100.00",
        ),
    )


async def test_insert_then_get_recent_round_trip(session: AsyncSession) -> None:
    await insert_trades(session, [_trade(1, "100.00"), _trade(2, "101.50")])
    await session.commit()  # caller owns the transaction; insert_trades doesn't commit

    recent = await get_recent_trades(session, "BTCUSDT", limit=10)

    assert [t.id for t in recent] == [2, 1]  # newest (latest timestamp) first
    assert recent[0].price == Decimal("101.50")  # exact Decimal survives the round-trip


async def test_insert_is_idempotent(session: AsyncSession) -> None:
    batch = [_trade(1, "100.00"), _trade(2, "101.50")]
    await insert_trades(session, batch)
    await session.commit()
    await insert_trades(session, batch)
    await session.commit()
    assert len(await get_recent_trades(session, "BTCUSDT", limit=100)) == len(batch)


async def test_insert_decimal_precision(session: AsyncSession) -> None:
    trade = _trade(1, "0.000000010000000001")
    await insert_trades(session, [trade])
    await session.commit()
    recent = await get_recent_trades(session, "BTCUSDT", limit=1)
    assert recent[0].price == Decimal("0.000000010000000001")


async def test_insert_tz_aware_utc_timestamp(session: AsyncSession) -> None:
    trade = _trade(1, "100.00")
    await insert_trades(session, [trade])
    await session.commit()
    recent = await get_recent_trades(session, "BTCUSDT", limit=1)

    assert recent[0].timestamp.tzinfo is not None
    assert recent[0].timestamp.tzinfo == UTC


async def test_get_trades_since_returns_only_in_window(session: AsyncSession) -> None:
    # ids 1..3 → timestamps 12:00:01, :02, :03
    await insert_trades(session, [_trade(1, "100"), _trade(2, "101"), _trade(3, "102")])
    await session.commit()

    since = datetime(2026, 1, 1, 12, 0, 2, tzinfo=UTC)
    result = await get_trades_since(session, "BTCUSDT", since)

    # >= since includes id 2 (the boundary); ascending order
    assert [t.id for t in result] == [2, 3]


async def test_metric_round_trip_populated(session: AsyncSession) -> None:
    snap = _snapshot(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        vwap=Decimal("100.5"),
        volatility=Decimal("0.0200"),
        ohlcv=_bar(),
    )
    await insert_metric(session, snap)
    await session.commit()

    rows = (await session.execute(select(MetricRow))).scalars().all()
    assert len(rows) == 1
    assert row_to_snapshot(rows[0]) == snap


async def test_metric_round_trip_nulls_survive(session: AsyncSession) -> None:
    # vwap/volatility/ohlcv None must survive as SQL NULL and rebuild as None.
    snap = _snapshot(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        vwap=None,
        volatility=None,
        ohlcv=None,
    )
    await insert_metric(session, snap)
    await session.commit()

    rows = (await session.execute(select(MetricRow))).scalars().all()
    restored = row_to_snapshot(rows[0])
    assert restored == snap
    assert restored.vwap is None
    assert restored.ohlcv is None


async def test_metric_insert_is_idempotent(session: AsyncSession) -> None:
    snap = _snapshot(
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        vwap=Decimal("100.5"),
        volatility=Decimal("0.02"),
        ohlcv=_bar(),
    )
    await insert_metric(session, snap)
    await session.commit()
    await insert_metric(session, snap)
    await session.commit()

    rows = (await session.execute(select(MetricRow))).scalars().all()
    assert len(rows) == 1


async def test_anomaly_round_trip(session: AsyncSession) -> None:
    event = _event(datetime(2026, 1, 1, 12, 0, tzinfo=UTC), z_score=Decimal("15.0"))
    await insert_anomaly(session, event)
    await session.commit()

    rows = (await session.execute(select(AnomalyRow))).scalars().all()
    assert len(rows) == 1
    assert row_to_event(rows[0]) == event


async def test_anomaly_round_trip_null_zscore_survives(session: AsyncSession) -> None:
    # The σ=0 case: z_score None must survive the DB round-trip.
    event = _event(datetime(2026, 1, 1, 12, 0, tzinfo=UTC), z_score=None)
    await insert_anomaly(session, event)
    await session.commit()

    rows = (await session.execute(select(AnomalyRow))).scalars().all()
    restored = row_to_event(rows[0])
    assert restored == event
    assert restored.anomaly.z_score is None
