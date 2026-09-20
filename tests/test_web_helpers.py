"""Tests for pyzdata._web_helpers — the Streamlit-free half of the web app."""

import io
from datetime import date

import pandas as pd
import pytest

from pyzdata._web_helpers import (
    DERIVATIVE_EXCHANGES,
    EXCHANGES,
    INTERVALS,
    MAIN_INTERVALS,
    PERIODS,
    POPULAR,
    chart_frame,
    contract_options,
    file_stem,
    friendly_error,
    instrument_options,
    period_to_dates,
    to_excel_bytes,
    underlyings,
)
from pyzdata.models import Interval


@pytest.fixture
def instruments() -> pd.DataFrame:
    rows = [
        # token, tradingsymbol, exchange, name, expiry, strike, instrument_type
        (1, "ZOMATO",        "NSE", "ZOMATO",              None,         0.0,   "EQ"),
        (2, "RELIANCE",      "NSE", "RELIANCE INDUSTRIES", None,         0.0,   "EQ"),
        (3, "NIFTY 50",      "NSE", "NIFTY 50",            None,         0.0,   "EQ"),
        (4, "ABB",           "NSE", None,                  None,         0.0,   "EQ"),
        (10, "0IRFC35-N0",   "NSE", "IRFC BOND",           None,         0.0,   "EQ"),
        (5, "RELIANCE",      "BSE", "RELIANCE INDUSTRIES", None,         0.0,   "EQ"),
        (6, "NIFTY24FEBFUT", "NFO", "NIFTY",               "2024-02-29", 0.0,   "FUT"),
        (7, "NIFTY24JANFUT", "NFO", "NIFTY",               "2024-01-25", 0.0,   "FUT"),
        (8, "NIFTY24JAN21500CE", "NFO", "NIFTY",           "2024-01-25", 21500, "CE"),
        (9, "ACC24JANFUT",   "NFO", "ACC",                 "2024-01-25", 0.0,   "FUT"),
    ]
    return pd.DataFrame(rows, columns=[
        "instrument_token", "tradingsymbol", "exchange", "name",
        "expiry", "strike", "instrument_type",
    ])


# ── Static tables ───────────────────────────────────────────────────────────


class TestTables:
    def test_derivative_exchanges_are_known_exchanges(self):
        assert DERIVATIVE_EXCHANGES <= set(EXCHANGES)

    def test_popular_symbols_use_cash_exchanges(self):
        assert set(POPULAR) <= set(EXCHANGES) - DERIVATIVE_EXCHANGES

    def test_every_interval_is_offered(self):
        assert set(INTERVALS.values()) == set(Interval)

    def test_main_intervals_are_a_subset_starting_with_day(self):
        assert MAIN_INTERVALS[0] == "Day"
        assert set(MAIN_INTERVALS) <= set(INTERVALS)

    def test_periods_are_ascending(self):
        days = list(PERIODS.values())
        assert days == sorted(days) and days[0] > 0


# ── period_to_dates ─────────────────────────────────────────────────────────


class TestPeriodToDates:
    def test_one_week(self):
        assert period_to_dates("1W", today=date(2024, 3, 15)) == (date(2024, 3, 8), date(2024, 3, 15))

    def test_five_years(self):
        start, end = period_to_dates("5Y", today=date(2024, 3, 15))
        assert (end - start).days == 1825

    def test_unknown_label_raises(self):
        with pytest.raises(KeyError):
            period_to_dates("Custom", today=date(2024, 3, 15))


# ── Instrument pickers ──────────────────────────────────────────────────────


class TestInstrumentOptions:
    def test_only_the_requested_exchange(self, instruments):
        assert set(instrument_options(instruments, "BSE")) == {"RELIANCE"}

    def test_popular_first_then_alphabetical_with_numeric_symbols_last(self, instruments):
        assert list(instrument_options(instruments, "NSE")) == [
            "NIFTY 50", "RELIANCE", "ABB", "ZOMATO", "0IRFC35-N0",
        ]

    def test_label_includes_company_name(self, instruments):
        assert instrument_options(instruments, "NSE")["RELIANCE"] == "RELIANCE — RELIANCE INDUSTRIES"

    def test_label_is_just_the_symbol_when_name_adds_nothing(self, instruments):
        options = instrument_options(instruments, "NSE")
        assert options["ZOMATO"] == "ZOMATO"
        assert options["ABB"] == "ABB"


class TestDerivativePickers:
    def test_underlyings_popular_first(self, instruments):
        assert underlyings(instruments, "NFO") == ["NIFTY", "ACC"]

    def test_futures_first_then_options_each_by_expiry(self, instruments):
        assert list(contract_options(instruments, "NFO", "NIFTY")) == [
            "NIFTY24JANFUT", "NIFTY24FEBFUT", "NIFTY24JAN21500CE",
        ]

    def test_contract_label_shows_type_and_expiry(self, instruments):
        label = contract_options(instruments, "NFO", "NIFTY")["NIFTY24JANFUT"]
        assert "FUT" in label and "25 Jan 2024" in label


# ── friendly_error ──────────────────────────────────────────────────────────


class TestFriendlyError:
    @pytest.mark.parametrize("raw, expected", [
        ("Login failed (HTTP 403). Check your user_id and password.", "Wrong User ID or password"),
        ("2FA rejected by Kite: Invalid TOTP", "TOTP"),
        ("Invalid or expired enctoken (HTTP 403).", "enctoken has expired"),
        ("Network error during login: timed out", "internet connection"),
        ("Network error during 2FA: reset", "internet connection"),
        ("Network error while checking the enctoken: reset", "internet connection"),
    ])
    def test_known_errors(self, raw, expected):
        assert expected in friendly_error(raw)

    def test_unknown_error_is_returned_as_is(self):
        assert friendly_error("Something odd") == "Something odd"


# ── Result helpers ──────────────────────────────────────────────────────────


def _candles(n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "tradingsymbol": "NIFTY 50",
        "datetime": pd.date_range("2024-01-01 09:15", periods=n, freq="min"),
        "close": range(n),
    })


class TestChartFrame:
    def test_small_frames_are_untouched(self):
        assert len(chart_frame(_candles(100))) == 100

    def test_large_frames_are_downsampled(self):
        chart = chart_frame(_candles(10_000), max_points=500)
        assert len(chart) <= 501

    def test_last_candle_is_always_kept(self):
        chart = chart_frame(_candles(10_000), max_points=500)
        assert chart["close"].iloc[-1] == 9_999

    def test_indexed_by_datetime_with_close_only(self):
        chart = chart_frame(_candles(10))
        assert chart.index.name == "datetime"
        assert list(chart.columns) == ["close"]


class TestFileStem:
    def test_spaces_replaced_and_dates_appended(self):
        assert file_stem("NIFTY 50", _candles(3), "Day") == "NIFTY_50_Day_2024-01-01_2024-01-01"

    def test_interval_label_is_made_filename_safe(self):
        assert "_1_min_" in file_stem("TCS", _candles(3), "1 min")


class TestToExcelBytes:
    def test_round_trips_through_openpyxl(self):
        raw = to_excel_bytes(_candles(5))
        back = pd.read_excel(io.BytesIO(raw))
        assert len(back) == 5
        assert list(back.columns) == ["tradingsymbol", "datetime", "close"]
