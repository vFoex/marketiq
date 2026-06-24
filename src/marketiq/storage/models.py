from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from marketiq.storage.database import Base


class TradeRow(Base):
    __tablename__ = "trades"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric)
    quantity: Mapped[Decimal] = mapped_column(Numeric)
    is_buyer_maker: Mapped[bool] = mapped_column(Boolean)

    __table_args__ = (Index("ix_trades_symbol_timestamp", "symbol", "timestamp"),)


class MetricRow(Base):
    __tablename__ = "metrics"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    window_seconds: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vwap: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    volume: Mapped[Decimal] = mapped_column(Numeric)
    volatility: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    open_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    high_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    low_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    close_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)


class AnomalyRow(Base):
    __tablename__ = "anomalies"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    kind: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric)
    mean: Mapped[Decimal] = mapped_column(Numeric)
    std_dev: Mapped[Decimal] = mapped_column(Numeric)
    z_score: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    reason: Mapped[str] = mapped_column(String)
