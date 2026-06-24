import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from marketiq.domain.trade import Trade
from marketiq.processing.anomalies import (
    Anomaly,
    AnomalyEvent,
    price_spike,
    volume_spike,
)
from marketiq.processing.metrics import (
    MetricSnapshot,
    ohlcv,
    realized_volatility,
    volume,
    vwap,
)
from marketiq.storage.database import session_scope
from marketiq.storage.repository import get_trades_since, insert_anomaly, insert_metric

logger = logging.getLogger(__name__)


def process_window(
    symbol: str, trades: list[Trade], window_seconds: int, computed_at: datetime
) -> tuple[MetricSnapshot | None, list[AnomalyEvent]]:

    if not trades or len(trades) == 0:
        return None, []

    snapshot = _compute_metrics(symbol, trades, window_seconds, computed_at)
    detected_at = max(trades, key=lambda t: t.timestamp).timestamp
    anomalies = _detect_anomalies(symbol, trades, detected_at)
    return snapshot, anomalies


async def process_once(
    session: AsyncSession, symbol: str, window_seconds: int, now: datetime
) -> None:
    since = now - timedelta(seconds=window_seconds)
    trades = await get_trades_since(session, symbol, since)
    snapshot, events = process_window(symbol, trades, window_seconds, now)
    logger.info(
        "process_once symbol=%s trades=%d snapshot=%s events=%d",
        symbol,
        len(trades),
        snapshot is not None,
        len(events),
    )
    if snapshot is not None:
        await insert_metric(session, snapshot)
    for event in events:
        await insert_anomaly(session, event)


async def run_processing(
    symbols: list[str], window_seconds: int, interval_seconds: float
) -> None:
    while True:
        now = datetime.now(UTC)
        for symbol in symbols:
            async with session_scope() as session:
                await process_once(session, symbol, window_seconds, now)
        await asyncio.sleep(interval_seconds)


def _compute_metrics(
    symbol: str, trades: list[Trade], window_seconds: int, computed_at: datetime
) -> MetricSnapshot:
    return MetricSnapshot(
        symbol=symbol,
        computed_at=computed_at,
        window_seconds=window_seconds,
        vwap=vwap(trades),
        volume=volume(trades),
        volatility=realized_volatility(trades),
        ohlcv=ohlcv(trades),
    )


def _detect_anomalies(
    symbol: str, trades: list[Trade], detected_at: datetime
) -> list[AnomalyEvent]:
    price_spike_anomaly = price_spike(trades)
    volume_spike_anomaly = volume_spike(trades)
    anomalies: list[Anomaly] = []
    if price_spike_anomaly:
        anomalies.append(price_spike_anomaly)
    if volume_spike_anomaly:
        anomalies.append(volume_spike_anomaly)

    return [
        AnomalyEvent(
            symbol=symbol,
            detected_at=detected_at,
            anomaly=anomaly,
        )
        for anomaly in anomalies
    ]
