from pydantic import BaseModel


class BinanceAggTrade(BaseModel):
    """Binance aggregate trade model."""

    a: int  # Aggregate trade ID
    s: str  # Symbol of the trade
    p: str  # Price
    q: str  # Quantity
    T: int  # Timestamp
    m: bool  # Is the buyer the market maker?
