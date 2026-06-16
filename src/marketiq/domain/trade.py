from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class Trade(BaseModel):
    """
    Trade model representing a trade in the market.

    Attributes:
        id (int): Unique identifier for the trade.
        symbol (str): The trading symbol (e.g., stock ticker).
        price (Decimal): The price at which the trade was executed.
        quantity (Decimal): The number of shares or contracts traded.
        timestamp (datetime): The timestamp of when the trade occurred.
        is_buyer_maker (bool): Indicates if the buyer is
         the maker of the trade (optional).
    """

    model_config = ConfigDict(frozen=True)

    id: int
    symbol: str
    price: Decimal
    quantity: Decimal
    timestamp: datetime
    is_buyer_maker: bool
