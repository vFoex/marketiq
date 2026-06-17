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
