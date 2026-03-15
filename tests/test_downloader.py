"""Unit tests for DataDownloader and its module-level helpers."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from pyzdata.downloader import (
    DataDownloader,
    _clean,
    _expected_cols,
    _month_windows,
    _parse_datetime,
)
from pyzdata.exceptions import DataFetchError
from pyzdata.models import Interval

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api_resp(candles: list, status: str = "success"):
    """Build a mock response with a Kite-style candle payload."""
    r = MagicMock(spec=requests.Response)
    r.status_code = 200
    r.raise_for_status.return_value = None
    r.json.return_value = {"status": status, "data": {"candles": candles}}
    return r


def _http_error_resp(status_code: int):
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    http_err = requests.HTTPError(response=r)
    r.raise_for_status.side_effect = http_err
    return r


@pytest.fixture
def instruments_stub():
    m = MagicMock()
    m.get_symbol.return_value = "RELIANCE"
    return m


@pytest.fixture
def downloader(mock_session, config, instruments_stub):
    return DataDownloader(
        session=mock_session,
        auth_headers={"Authorization": "enctoken test"},
        instruments=instruments_stub,
        config=config,
    )


# ---------------------------------------------------------------------------
# _month_windows (pure helper)
# ---------------------------------------------------------------------------

class TestMonthWindows:

    def test_single_day(self):
        windows = list(_month_windows(pd.Timestamp("2024-01-15"), pd.Timestamp("2024-01-15")))
        assert len(windows) == 1
        assert windows[0][0].date() == date(2024, 1, 15)
        assert windows[0][1].date() == date(2024, 1, 15)

    def test_single_month_mid_range(self):
        windows = list(_month_windows(pd.Timestamp("2024-01-10"), pd.Timestamp("2024-01-20")))
        assert len(windows) == 1
        start, end = windows[0]
        assert start.date() == date(2024, 1, 10)
        assert end.date()   == date(2024, 1, 20)

    def test_two_months(self):
        windows = list(_month_windows(pd.Timestamp("2024-01-15"), pd.Timestamp("2024-02-10")))
        assert len(windows) == 2
        assert windows[0][0].date() == date(2024, 1, 15)
        assert windows[0][1].date() == date(2024, 1, 31)
        assert windows[1][0].date() == date(2024, 2,  1)
        assert windows[1][1].date() == date(2024, 2, 10)

    def test_full_year_produces_12_windows(self):
        windows = list(_month_windows(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31")))
        assert len(windows) == 12

    def test_feb_leap_year(self):
        windows = list(_month_windows(pd.Timestamp("2024-02-01"), pd.Timestamp("2024-02-29")))
        assert len(windows) == 1
        assert windows[0][1].date() == date(2024, 2, 29)

    def test_cross_year_boundary(self):
        windows = list(_month_windows(pd.Timestamp("2023-12-15"), pd.Timestamp("2024-01-10")))
        assert len(windows) == 2
        assert windows[0][0].year == 2023
        assert windows[1][0].year == 2024


# ---------------------------------------------------------------------------
# _parse_datetime (pure helper)
# ---------------------------------------------------------------------------

class TestParseDatetime:

    def test_strips_ist_timezone(self):
        df = pd.DataFrame({"datetime": ["2024-01-02T09:15:00+0530"]})
        result = _parse_datetime(df)
        assert result["datetime"].dt.tz is None

    def test_naive_timestamps_unchanged(self):
        df = pd.DataFrame({"datetime": ["2024-01-02 09:15:00"]})
        result = _parse_datetime(df)
        assert result["datetime"].dt.tz is None

    def test_correct_ist_value(self):
        """09:15 IST should remain 09:15 after tz-stripping."""
        df = pd.DataFrame({"datetime": ["2024-01-02T09:15:00+0530"]})
        result = _parse_datetime(df)
        assert result["datetime"].iloc[0].hour == 9
        assert result["datetime"].iloc[0].minute == 15


# ---------------------------------------------------------------------------
# _clean (pure helper)
# ---------------------------------------------------------------------------

class TestClean:

    def _make_df(self, timestamps):
        return pd.DataFrame({
            "datetime": pd.to_datetime(timestamps),
            "close":    [100.0] * len(timestamps),
        })

    def test_deduplication(self):
        df = self._make_df(["2024-01-02 09:15:00", "2024-01-02 09:15:00"])
        result = _clean(df, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-02"))
        assert len(result) == 1

    def test_clips_to_range(self):
        df = self._make_df([
            "2024-01-01 09:15:00",  # before range
            "2024-01-02 09:15:00",  # in range
            "2024-01-03 09:15:00",  # after range
        ])
        result = _clean(df, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-02"))
        assert len(result) == 1
        assert result.iloc[0]["datetime"].date() == date(2024, 1, 2)

    def test_sorted_ascending(self):
        df = self._make_df([
            "2024-01-02 09:17:00",
            "2024-01-02 09:15:00",
            "2024-01-02 09:16:00",
        ])
        result = _clean(df, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-02"))
        times = result["datetime"].tolist()
        assert times == sorted(times)


# ---------------------------------------------------------------------------
# DataDownloader.fetch
# ---------------------------------------------------------------------------

class TestFetch:

    def test_success_returns_dataframe(self, downloader, mock_session, sample_candles):
        mock_session.get.return_value = _api_resp(sample_candles)
        df = downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.MINUTE_1)

        assert not df.empty
        assert "tradingsymbol" in df.columns
        assert "datetime" in df.columns
        assert df["tradingsymbol"].iloc[0] == "RELIANCE"

    def test_empty_candles_returns_empty_df(self, downloader, mock_session):
        mock_session.get.return_value = _api_resp([])
        df = downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.DAY)
        assert df.empty
        # Empty DF should still have the right columns
        assert "datetime" in df.columns

    def test_http_500_raises_data_fetch_error(self, downloader, mock_session):
        mock_session.get.return_value = _http_error_resp(500)
        with pytest.raises(DataFetchError, match="HTTP 500"):
            downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.DAY)

    def test_api_error_status_raises(self, downloader, mock_session):
        mock_session.get.return_value = _api_resp([], status="error")
        # Override json to include message
        resp = mock_session.get.return_value
        resp.json.return_value = {"status": "error", "message": "Too many requests"}
        with pytest.raises(DataFetchError, match="Too many requests"):
            downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.DAY)

    def test_invalid_date_range_raises(self, downloader):
        with pytest.raises(ValueError, match="must not be after"):
            downloader.fetch(408065, "2024-01-31", "2024-01-01", Interval.DAY)

    def test_column_count_mismatch_raises(self, downloader, mock_session):
        """7 columns when oi=False expects 6 → DataFetchError."""
        bad_candles = [
            ["2024-01-02T09:15:00+0530", 100, 101, 99, 100, 5000, 99999]
        ]
        mock_session.get.return_value = _api_resp(bad_candles)
        with pytest.raises(DataFetchError, match="column count"):
            downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.MINUTE_1, oi=False)

    def test_deduplication(self, downloader, mock_session, sample_candles):
        """Duplicate candles from the API should be removed."""
        mock_session.get.return_value = _api_resp(sample_candles * 2)
        df = downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.MINUTE_1)
        assert len(df) == len(sample_candles)

    def test_oi_columns_present_when_requested(self, downloader, mock_session, sample_candles_oi):
        mock_session.get.return_value = _api_resp(sample_candles_oi)
        df = downloader.fetch(884737, "2024-01-02", "2024-01-04", Interval.DAY, oi=True)
        assert "open_interest" in df.columns

    def test_sorted_chronologically(self, downloader, mock_session, sample_candles):
        # Reverse the candles so they arrive out of order
        mock_session.get.return_value = _api_resp(list(reversed(sample_candles)))
        df = downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.MINUTE_1)
        times = df["datetime"].tolist()
        assert times == sorted(times)

    def test_network_error_raises_data_fetch_error(self, downloader, mock_session):
        mock_session.get.side_effect = requests.ConnectionError("unreachable")
        with pytest.raises(DataFetchError, match="Network error"):
            downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.DAY)


# ---------------------------------------------------------------------------
# _expected_cols helper
# ---------------------------------------------------------------------------

class TestExpectedCols:

    def test_without_oi(self):
        cols = _expected_cols(False)
        assert "open_interest" not in cols
        assert len(cols) == 6

    def test_with_oi(self):
        cols = _expected_cols(True)
        assert cols[-1] == "open_interest"
        assert len(cols) == 7
