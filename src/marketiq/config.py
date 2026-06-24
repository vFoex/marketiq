from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    binance_ws_url: str
    binance_rest_url: str
    symbols: list[str] = ["BTCUSDT"]
    batch_size: int = 100
    flush_interval_seconds: float = 1.0
    metrics_window_seconds: int = 60
    metrics_interval_seconds: float = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
