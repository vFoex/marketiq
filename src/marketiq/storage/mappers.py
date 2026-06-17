from marketiq.domain.trade import Trade
from marketiq.storage.models import TradeRow


def to_row(trade: Trade) -> TradeRow:
    return TradeRow(
        id=trade.id,
        symbol=trade.symbol,
        price=trade.price,
        quantity=trade.quantity,
        timestamp=trade.timestamp,
        is_buyer_maker=trade.is_buyer_maker,
    )


def to_domain(row: TradeRow) -> Trade:
    trade: Trade = Trade(
        id=row.id,
        symbol=row.symbol,
        price=row.price,
        quantity=row.quantity,
        timestamp=row.timestamp,
        is_buyer_maker=row.is_buyer_maker,
    )
    return trade
