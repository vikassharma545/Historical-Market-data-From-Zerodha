"""Streamlit-free helpers for the web interface.

Everything here is plain data and pure functions so it can be unit-tested
without a running Streamlit session.  The UI itself lives in :mod:`pyzdata._app`.
"""

from __future__ import annotations

import io
import re
from datetime import date, timedelta
from typing import Dict, List, Tuple

import pandas as pd

from .models import Interval

# ─────────────────────────────────────────────────────────────────────────────
# Static tables
# ─────────────────────────────────────────────────────────────────────────────

EXCHANGES: List[str] = ["NSE", "BSE", "NFO", "BFO", "MCX", "CDS"]

#: Exchanges that list dated contracts.  They get the two-step picker
#: (underlying → contract) and the open-interest option.
DERIVATIVE_EXCHANGES = frozenset({"NFO", "BFO", "MCX", "CDS"})

EXCHANGE_HELP = (
    "NSE / BSE — stocks and indices.  NFO / BFO — futures & options.  "
    "MCX — commodities.  CDS — currency."
)

#: Shown at the top of the stock dropdown so the common picks need no typing.
POPULAR: Dict[str, List[str]] = {
    "NSE": [
        "NIFTY 50", "NIFTY BANK", "RELIANCE", "TCS", "HDFCBANK", "INFY",
        "ICICIBANK", "SBIN", "ITC", "BAJFINANCE", "AXISBANK", "MARUTI",
    ],
    "BSE": ["SENSEX", "RELIANCE", "TCS", "HDFCBANK", "INFY"],
}

_POPULAR_UNDERLYINGS: List[str] = [
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX",
    "CRUDEOIL", "NATURALGAS", "GOLD", "SILVER", "USDINR",
]

#: Period label → days back from today.  "Custom" is handled by the UI.
PERIODS: Dict[str, int] = {
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 182,
    "1Y": 365,
    "3Y": 1095,
    "5Y": 1825,
}

#: Every interval the library supports, by display label.
INTERVALS: Dict[str, Interval] = {
    "Day":     Interval.DAY,
    "1 hour":  Interval.HOUR_1,
    "30 min":  Interval.MINUTE_30,
    "15 min":  Interval.MINUTE_15,
    "5 min":   Interval.MINUTE_5,
    "1 min":   Interval.MINUTE_1,
    "2 min":   Interval.MINUTE_2,
    "3 min":   Interval.MINUTE_3,
    "4 min":   Interval.MINUTE_4,
    "10 min":  Interval.MINUTE_10,
    "2 hours": Interval.HOUR_2,
    "3 hours": Interval.HOUR_3,
    "4 hours": Interval.HOUR_4,
}

#: The intervals shown as one-click pills; the rest sit behind "Other".
MAIN_INTERVALS: List[str] = ["Day", "1 hour", "30 min", "15 min", "5 min", "1 min"]

#: Excel worksheets hold 1,048,576 rows including the header.
EXCEL_MAX_ROWS = 1_048_575


def period_to_dates(label: str, today: date) -> Tuple[date, date]:
    """Turn a :data:`PERIODS` label into a ``(start, end)`` date pair."""
    return today - timedelta(days=PERIODS[label]), today


# ─────────────────────────────────────────────────────────────────────────────
# Instrument pickers
# ─────────────────────────────────────────────────────────────────────────────

def _popular_first(values: List[str], popular: List[str]) -> List[str]:
    present = set(values)
    head = [v for v in popular if v in present]
    return head + sorted(present - set(head))


def instrument_options(instruments: pd.DataFrame, exchange: str) -> Dict[str, str]:
    """``{tradingsymbol: label}`` for a cash exchange, popular symbols first."""
    rows = instruments[instruments["exchange"] == exchange]
    names = dict(zip(rows["tradingsymbol"].astype(str), rows["name"]))

    def label(symbol: str) -> str:
        name = names[symbol]
        if isinstance(name, str) and name.strip() and name.strip() != symbol:
            return f"{symbol} — {name.strip()}"
        return symbol

    ordered = _popular_first(list(names), POPULAR.get(exchange, []))
    return {symbol: label(symbol) for symbol in ordered}


def underlyings(instruments: pd.DataFrame, exchange: str) -> List[str]:
    """Underlying names (NIFTY, CRUDEOIL …) on a derivatives exchange."""
    rows = instruments[instruments["exchange"] == exchange]
    names = rows["name"].dropna().astype(str).unique().tolist()
    return _popular_first(names, _POPULAR_UNDERLYINGS)


def contract_options(
    instruments: pd.DataFrame, exchange: str, underlying: str
) -> Dict[str, str]:
    """``{tradingsymbol: label}`` for one underlying: nearest expiry first,
    futures ahead of options, options by strike."""
    rows = instruments[
        (instruments["exchange"] == exchange) & (instruments["name"] == underlying)
    ].copy()
    rows["_expiry"] = pd.to_datetime(rows["expiry"], errors="coerce")
    rows["_is_option"] = rows["instrument_type"] != "FUT"
    rows = rows.sort_values(["_expiry", "_is_option", "strike", "tradingsymbol"])

    options: Dict[str, str] = {}
    for symbol, kind, expiry in zip(rows["tradingsymbol"], rows["instrument_type"], rows["_expiry"]):
        when = f" · expires {expiry:%d %b %Y}" if pd.notna(expiry) else ""
        options[str(symbol)] = f"{symbol} — {kind}{when}"
    return options


# ─────────────────────────────────────────────────────────────────────────────
# Messages
# ─────────────────────────────────────────────────────────────────────────────

def friendly_error(message: str) -> str:
    """Translate a library error message into plain English."""
    text = message.lower()
    # Network first: those messages also mention the step that was interrupted.
    if "network" in text or "connect" in text or "timed out" in text:
        return "Could not reach Zerodha. Check your internet connection and try again."
    if "enctoken" in text:
        return (
            "That enctoken has expired or is not valid. Log in to kite.zerodha.com "
            "again and copy a fresh one."
        )
    if "totp" in text or "2fa" in text or "twofa" in text:
        return "Wrong TOTP code. Open your authenticator app and use the latest 6-digit code."
    if "403" in text or "password" in text:
        return "Wrong User ID or password. Please check and try again."
    return message


# ─────────────────────────────────────────────────────────────────────────────
# Download results
# ─────────────────────────────────────────────────────────────────────────────

def chart_frame(df: pd.DataFrame, max_points: int = 2000) -> pd.DataFrame:
    """Closing prices indexed by time, thinned to about *max_points* rows.

    A browser chart gains nothing from 400k points, and Streamlit keeps
    whatever we store in session state — so keep it small.
    """
    chart = df[["datetime", "close"]]
    step = -(-len(chart) // max_points)  # ceil division
    if step > 1:
        last = chart.iloc[[-1]]
        chart = chart.iloc[::step]
        if chart.index[-1] != last.index[-1]:
            chart = pd.concat([chart, last])
    return chart.set_index("datetime")


def file_stem(symbol: str, df: pd.DataFrame, interval_label: str) -> str:
    """``NIFTY_50_Day_2024-01-01_2024-12-31`` — a safe, descriptive file name."""
    safe = re.sub(r"[^A-Za-z0-9]+", "_", f"{symbol} {interval_label}").strip("_")
    return f"{safe}_{df['datetime'].min().date()}_{df['datetime'].max().date()}"


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise *df* as an ``.xlsx`` workbook (requires ``openpyxl``)."""
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name="data", engine="openpyxl")
    return buffer.getvalue()
