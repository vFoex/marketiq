from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.processing.anomalies import AnomalyEvent
from marketiq.processing.metrics import MetricSnapshot
from marketiq.storage.mappers import event_to_row, row_to_trade, snapshot_to_row
from marketiq.storage.models import AnomalyRow, MetricRow, TradeRow


async def insert_trades(session: AsyncSession, trades: list[Trade]) -> None:
    if not trades or len(trades) == 0:
        return

    stmt = pg_insert(TradeRow).values([t.model_dump() for t in trades])
    stmt = stmt.on_conflict_do_nothing(index_elements=["symbol", "id", "timestamp"])
    await session.execute(stmt)


async def get_recent_trades(
    session: AsyncSession, symbol: str, limit: int
) -> list[Trade]:
    stmt = (
        select(TradeRow)
        .where(TradeRow.symbol == symbol)
        .order_by(TradeRow.timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [row_to_trade(row) for row in result.scalars().all()]


async def get_trades_since(
    session: AsyncSession, symbol: str, since: datetime
) -> list[Trade]:
    stmt = (
        select(TradeRow)
        .where(TradeRow.symbol == symbol)
        .where(TradeRow.timestamp >= since)
        .order_by(TradeRow.timestamp.asc())
    )
    result = await session.execute(stmt)
    return [row_to_trade(row) for row in result.scalars().all()]


async def insert_metric(session: AsyncSession, snapshot: MetricSnapshot) -> None:
    row: MetricRow = snapshot_to_row(snapshot)
    stmt = (
        pg_insert(MetricRow)
        .values({c.key: getattr(row, c.key) for c in MetricRow.__table__.columns})
        .on_conflict_do_nothing(
            index_elements=["symbol", "computed_at", "window_seconds"]
        )
    )
    await session.execute(stmt)


async def insert_anomaly(session: AsyncSession, event: AnomalyEvent) -> None:
    row = event_to_row(event)
    stmt = (
        pg_insert(AnomalyRow)
        .values({c.key: getattr(row, c.key) for c in AnomalyRow.__table__.columns})
        .on_conflict_do_nothing(index_elements=["symbol", "detected_at", "kind"])
    )
    await session.execute(stmt)
