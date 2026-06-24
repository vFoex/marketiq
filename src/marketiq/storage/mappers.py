from marketiq.domain.trade import Trade
from marketiq.processing.anomalies import Anomaly, AnomalyEvent
from marketiq.processing.metrics import OHLCV, MetricSnapshot
from marketiq.storage.models import AnomalyRow, MetricRow, TradeRow


def trade_to_row(trade: Trade) -> TradeRow:
    return TradeRow(
        id=trade.id,
        symbol=trade.symbol,
        price=trade.price,
        quantity=trade.quantity,
        timestamp=trade.timestamp,
        is_buyer_maker=trade.is_buyer_maker,
    )


def row_to_trade(row: TradeRow) -> Trade:
    trade: Trade = Trade(
        id=row.id,
        symbol=row.symbol,
        price=row.price,
        quantity=row.quantity,
        timestamp=row.timestamp,
        is_buyer_maker=row.is_buyer_maker,
    )
    return trade


def snapshot_to_row(snap: MetricSnapshot) -> MetricRow:
    bar = snap.ohlcv
    return MetricRow(
        symbol=snap.symbol,
        computed_at=snap.computed_at,
        window_seconds=snap.window_seconds,
        vwap=snap.vwap,
        volume=snap.volume,
        volatility=snap.volatility,
        open_price=bar.open if bar else None,
        high_price=bar.high if bar else None,
        low_price=bar.low if bar else None,
        close_price=bar.close if bar else None,
    )


def row_to_snapshot(row: MetricRow) -> MetricSnapshot:
    bar = (
        OHLCV(
            open=row.open_price,
            high=row.high_price,
            low=row.low_price,
            close=row.close_price,
            volume=row.volume,
        )
        if row.open_price is not None
        else None
    )
    return MetricSnapshot(
        symbol=row.symbol,
        computed_at=row.computed_at,
        window_seconds=row.window_seconds,
        vwap=row.vwap,
        volume=row.volume,
        volatility=row.volatility,
        ohlcv=bar,
    )


def event_to_row(event: AnomalyEvent) -> AnomalyRow:
    return AnomalyRow(
        symbol=event.symbol,
        detected_at=event.detected_at,
        kind=event.anomaly.kind,
        value=event.anomaly.value,
        mean=event.anomaly.mean,
        std_dev=event.anomaly.std_dev,
        z_score=event.anomaly.z_score,
        reason=event.anomaly.reason,
    )


def row_to_event(row: AnomalyRow) -> AnomalyEvent:
    return AnomalyEvent(
        symbol=row.symbol,
        detected_at=row.detected_at,
        anomaly=Anomaly(
            kind=row.kind,
            value=row.value,
            mean=row.mean,
            std_dev=row.std_dev,
            z_score=row.z_score,
            reason=row.reason,
        ),
    )
