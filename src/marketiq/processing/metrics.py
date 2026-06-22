from decimal import Decimal

from marketiq.domain.trade import Trade


def vwap(trades: list[Trade]) -> Decimal | None:
    """Calculate the Volume Weighted Average Price for a batch of trades."""
    total_volume = sum(trade.quantity for trade in trades)
    if total_volume == 0:
        return None
    return sum(trade.price * trade.quantity for trade in trades) / total_volume
