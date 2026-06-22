from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from marketiq.domain.trade import Trade


class OHLCV(BaseModel):
    model_config = ConfigDict(frozen=True)
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def vwap(trades: list[Trade]) -> Decimal | None:
    """Calculate the Volume Weighted Average Price for a batch of trades."""
    total_volume = sum(trade.quantity for trade in trades)
    if total_volume == 0:
        return None
    return sum(trade.price * trade.quantity for trade in trades) / total_volume


def ohlcv(trades: list[Trade]) -> OHLCV | None:
    """Calculate the OHLCV for a batch of trades."""
    if not trades:
        return None
    open_price = min(trades, key=lambda t: t.timestamp).price
    close_price = max(trades, key=lambda t: t.timestamp).price
    high_price = max(trade.price for trade in trades)
    low_price = min(trade.price for trade in trades)
    total_volume = sum(trade.quantity for trade in trades)
    return OHLCV(
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=total_volume,
    )
