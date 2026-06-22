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


def volume(trades: list[Trade]) -> Decimal:
    """Total quantity traded across the given trades (0 when there are none)."""
    return sum((trade.quantity for trade in trades), Decimal("0"))


def vwap(trades: list[Trade]) -> Decimal | None:
    """Calculate the Volume Weighted Average Price for a batch of trades."""
    total_volume = volume(trades)
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
    return OHLCV(
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume(trades),
    )


def realized_volatility(trades: list[Trade]) -> Decimal | None:
    """Realized volatility: sqrt of the summed squared log returns.

    Uses the realized-variance definition (zero-mean assumption, standard for
    high-frequency data) — no de-meaning, no annualization. Stays in Decimal via
    Decimal.ln()/.sqrt(), deterministic to the active context precision.
    """
    if len(trades) < 2:
        return None
    ordered = sorted(trades, key=lambda t: (t.timestamp, t.id))
    log_returns = [
        (ordered[i].price / ordered[i - 1].price).ln() for i in range(1, len(ordered))
    ]
    realized_variance = sum((r**2 for r in log_returns), Decimal("0"))
    return realized_variance.sqrt()
