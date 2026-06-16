import pytest

from marketiq.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ignore any local .env so tests are reproducible (CI has none anyway),
    # and supply the required fields.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5433/marketiq")
    monkeypatch.setenv("BINANCE_WS_URL", "wss://stream.example/ws")
    monkeypatch.setenv("BINANCE_REST_URL", "https://api.example/v3")


def test_defaults_applied() -> None:
    s = Settings()
    assert s.symbols == ["BTCUSDT"]
    assert s.batch_size == 100
    assert s.flush_interval_seconds == 1.0


def test_symbols_parsed_from_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYMBOLS", '["BTCUSDT", "ETHUSDT"]')
    assert Settings().symbols == ["BTCUSDT", "ETHUSDT"]


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
