from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.storage.repository import get_recent_trades, insert_trades


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
