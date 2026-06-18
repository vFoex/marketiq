from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.storage.mappers import to_domain
from marketiq.storage.models import TradeRow


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
    return [to_domain(row) for row in result.scalars().all()]
