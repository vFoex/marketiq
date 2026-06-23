from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from marketiq.domain.trade import Trade

_PRICE_REASON = "price {latest} is {magnitude} {direction} mean {mean:.2f}"
_VOLUME_REASON = "volume {latest} is {magnitude} {direction} mean {mean:.2f}"


class Anomaly(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: str  # "price_spike" | "volume_spike"
    value: Decimal  # the observed point (exact)
    mean: Decimal  # baseline mean
    std_dev: Decimal
    z_score: Decimal | None  # how many σ out; None when the baseline is flat
    reason: str


def _zscore_spike(
    values: list[Decimal], threshold: Decimal, kind: str, reason_fmt: str
) -> Anomaly | None:
    """Flag the latest value if it sits >= threshold sigmas from the baseline.

    The baseline is every value *except* the latest, so an outlier cannot inflate
    its own statistics and mask itself.
    """
    if len(values) < 2:
        return None

    *baseline, latest = values
    n = len(baseline)
    mean = sum(baseline, Decimal("0")) / n
    variance = sum(((x - mean) ** 2 for x in baseline), Decimal("0")) / n
    std_dev = variance.sqrt()

    if std_dev == 0:
        if latest == mean:
            return None  # flat baseline, no movement → nothing to flag
        # Flat baseline that suddenly moves is a definite spike, but the z-score
        # is mathematically infinite — report magnitude as None rather than fake it.
        z_score: Decimal | None = None
        magnitude = "∞σ"
    else:
        z = (latest - mean) / std_dev
        if abs(z) < threshold:
            return None
        z_score = z
        magnitude = f"{abs(z):.2f}σ"

    direction = "above" if latest > mean else "below"
    reason = reason_fmt.format(
        latest=latest, mean=mean, magnitude=magnitude, direction=direction
    )
    return Anomaly(
        kind=kind,
        value=latest,
        mean=mean,
        std_dev=std_dev,
        z_score=z_score,
        reason=reason,
    )


def _time_ordered(trades: list[Trade]) -> list[Trade]:
    """Oldest first, so the latest trade is the point under test."""
    return sorted(trades, key=lambda t: (t.timestamp, t.id))


def price_spike(
    trades: list[Trade], threshold: Decimal = Decimal("3.0")
) -> Anomaly | None:
    prices = [t.price for t in _time_ordered(trades)]
    return _zscore_spike(prices, threshold, "price_spike", _PRICE_REASON)


def volume_spike(
    trades: list[Trade], threshold: Decimal = Decimal("3.0")
) -> Anomaly | None:
    volumes = [t.quantity for t in _time_ordered(trades)]
    return _zscore_spike(volumes, threshold, "volume_spike", _VOLUME_REASON)
