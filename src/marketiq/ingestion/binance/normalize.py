import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from marketiq.domain.trade import Trade
from marketiq.ingestion.binance.schemas import BinanceAggTrade


def normalize_binance_agg_trade(aggregate_trade: BinanceAggTrade) -> Trade:
    """
    Normalize a Binance aggregated trade into a Trade model.

    Returns:
        Trade: A normalized Trade model.
    """
    return Trade(
        id=aggregate_trade.a,
        symbol=aggregate_trade.s,
        price=Decimal(aggregate_trade.p),
        quantity=Decimal(aggregate_trade.q),
        timestamp=datetime.fromtimestamp(0, UTC)
        + timedelta(milliseconds=aggregate_trade.T),
        is_buyer_maker=aggregate_trade.m,
    )


def _event_to_trade(raw: str | bytes) -> Trade:
    event = json.loads(raw)
    data = event.get("data", event)  # unwrap combined-stream envelope; bare event too
    return normalize_binance_agg_trade(BinanceAggTrade(**data))
