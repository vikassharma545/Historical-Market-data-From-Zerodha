"""Data models and enumerations for PyZData."""

from enum import Enum


class Interval(Enum):
    """Candle intervals supported by the Zerodha Kite historical API.

    Usage::

        from pyzdata import Interval
        df = client.get_data(token, "2024-01-01", "2024-12-31", Interval.DAY)
    """

    MINUTE_1  = "minute"
    MINUTE_2  = "2minute"
    MINUTE_3  = "3minute"
    MINUTE_4  = "4minute"
    MINUTE_5  = "5minute"
    MINUTE_10 = "10minute"
    MINUTE_15 = "15minute"
    MINUTE_30 = "30minute"
    HOUR_1    = "60minute"
    HOUR_2    = "2hour"
    HOUR_3    = "3hour"
    HOUR_4    = "4hour"
    DAY       = "day"
