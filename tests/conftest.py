"""Shared pytest fixtures.

All tests use mocked HTTP sessions — no real network calls are made.
"""

from unittest.mock import MagicMock

import pytest
import requests

from pyzdata.config import Config


@pytest.fixture
def config(tmp_path) -> Config:
    """Config with sane test-time defaults.

    * max_retries=0       — fail fast; no exponential backoff delays in tests
    * instruments_cache_ttl_hours=0  — always treat cache as stale
    * instruments_cache_path         — use a temp dir, never ~/.pyzdata
    * max_workers=1                  — deterministic single-threaded execution
    """
    return Config(
        max_retries=0,
        request_timeout=5,
        instruments_cache_ttl_hours=0,
        instruments_cache_path=str(tmp_path / "instruments.csv"),
        max_workers=1,
        rate_limit_per_second=0,
        log_level="ERROR",
    )


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock(spec=requests.Session)


@pytest.fixture
def instruments_csv_text() -> str:
    """Minimal instruments CSV that mirrors the real Zerodha format."""
    return (
        "instrument_token,tradingsymbol,exchange,name,last_price,expiry,"
        "strike,tick_size,lot_size,instrument_type,segment\n"
        "256265,NIFTY 50,NSE,NIFTY 50 INDEX,0.0,,0.0,0.05,1,EQ,NSE\n"
        "408065,RELIANCE,NSE,RELIANCE INDUSTRIES,2500.0,,0.0,0.05,1,EQ,NSE\n"
        "884737,NIFTY24JANFUT,NFO,NIFTY FUTURES,21500.0,2024-01-25,0.0,0.05,50,FUT,NFO-FUT\n"
    )


@pytest.fixture
def sample_candles() -> list:
    """Six 1-minute OHLCV candles with IST timestamps."""
    return [
        ["2024-01-02T09:15:00+0530", 100.0, 101.0, 99.5,  100.5, 5000],
        ["2024-01-02T09:16:00+0530", 100.5, 102.0, 100.0, 101.0, 3000],
        ["2024-01-02T09:17:00+0530", 101.0, 101.5, 100.5, 101.0, 2000],
        ["2024-01-02T09:18:00+0530", 101.0, 103.0, 100.8, 102.5, 8000],
        ["2024-01-02T09:19:00+0530", 102.5, 103.5, 102.0, 103.0, 6000],
        ["2024-01-02T09:20:00+0530", 103.0, 104.0, 102.8, 103.5, 4000],
    ]


@pytest.fixture
def sample_candles_oi() -> list:
    """Three daily OHLCV+OI candles."""
    return [
        ["2024-01-02T00:00:00+0530", 21500.0, 21800.0, 21400.0, 21750.0, 1000000, 9500000],
        ["2024-01-03T00:00:00+0530", 21750.0, 22000.0, 21700.0, 21900.0,  950000, 9200000],
        ["2024-01-04T00:00:00+0530", 21900.0, 22100.0, 21850.0, 22050.0,  800000, 9100000],
    ]
