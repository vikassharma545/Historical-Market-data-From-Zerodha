"""PyZData – Zerodha historical market data downloader.

Quick start::

    from pyzdata import PyZData, Interval

    client = PyZData(enctoken="your_enctoken")

    token = client.get_instrument_token("NIFTY 50", "NSE")
    df    = client.get_data(token, "2024-01-01", "2024-12-31", Interval.DAY)
    print(df.head())
"""

from .client import PyZData
from .config import Config
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    DataFetchError,
    InstrumentNotFoundError,
    PyZDataError,
)
from .models import Interval

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    __version__ = _pkg_version("pyzdata")
except (PackageNotFoundError, ModuleNotFoundError):
    __version__ = "0.0.0-dev"

__all__ = [
    "PyZData",
    "Interval",
    "Config",
    "__version__",
    # Exceptions — exported so callers can write `except pyzdata.DataFetchError`
    "PyZDataError",
    "AuthenticationError",
    "InstrumentNotFoundError",
    "DataFetchError",
    "ConfigurationError",
]
