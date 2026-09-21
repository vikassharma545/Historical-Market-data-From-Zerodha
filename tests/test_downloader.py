"""Unit tests for DataDownloader and its module-level helpers."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from pyzdata.downloader import (
    DataDownloader,
    _clean,
    _date_windows,
    _expected_cols,
    _max_days,
    _parse_datetime,
)
from pyzdata.exceptions import DataFetchError, PartialDataError
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
# _date_windows / _max_days (pure helpers)
# ---------------------------------------------------------------------------

class TestDateWindows:

    def test_single_day(self):
        windows = list(_date_windows(pd.Timestamp("2024-01-15"), pd.Timestamp("2024-01-15"), 60))
        assert [(s.date(), e.date()) for s, e in windows] == [
            (date(2024, 1, 15), date(2024, 1, 15))
        ]

    def test_range_within_limit_is_one_window(self):
        windows = list(_date_windows(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-29"), 60))
        assert len(windows) == 1
        assert windows[0][1].date() == date(2024, 2, 29)

    def test_range_is_split_without_gaps_or_overlap(self):
        windows = list(_date_windows(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-05-31"), 60))
        assert [(s.date(), e.date()) for s, e in windows] == [
            (date(2024, 1, 1),  date(2024, 2, 29)),
            (date(2024, 3, 1),  date(2024, 4, 29)),
            (date(2024, 4, 30), date(2024, 5, 31)),
        ]

    def test_no_window_exceeds_max_days(self):
        windows = _date_windows(pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31"), 100)
        assert all((e - s).days + 1 <= 100 for s, e in windows)


class TestMaxDays:

    @pytest.mark.parametrize("interval, expected", [
        (Interval.MINUTE_1, 60),
        (Interval.MINUTE_3, 60),
        (Interval.MINUTE_5, 100),
        (Interval.MINUTE_10, 100),
        (Interval.MINUTE_15, 200),
        (Interval.MINUTE_30, 200),
        (Interval.HOUR_1, 400),
        (Interval.HOUR_4, 400),
        (Interval.DAY, 2000),
    ])
    def test_limits(self, interval, expected):
        assert _max_days(interval) == expected

    def test_every_interval_has_a_limit(self):
        for interval in Interval:
            assert _max_days(interval) > 0


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
# DataDownloader.fetch — multi-window behaviour
# ---------------------------------------------------------------------------

def _daily_candle(day: str) -> list:
    return [f"{day}T09:15:00+0530", 100.0, 101.0, 99.0, 100.5, 1000]


class TestFetchMultiWindow:
    """2024-01-01 → 2024-05-31 at 1-minute = three 60-day windows."""

    _ARGS = (408065, "2024-01-01", "2024-05-31", Interval.MINUTE_1)
    _GOOD = {
        "2024-01-01": _daily_candle("2024-01-02"),
        "2024-03-01": _daily_candle("2024-03-04"),
        "2024-04-30": _daily_candle("2024-05-02"),
    }

    def _serve(self, mock_session, failures: dict):
        """*failures* maps a window's start date → number of times it fails."""
        remaining = dict(failures)

        def _get(url, params, **kwargs):
            start = params["from"][:10]
            if remaining.get(start, 0) > 0:
                remaining[start] -= 1
                return _http_error_resp(500)
            return _api_resp([self._GOOD[start]])

        mock_session.get.side_effect = _get

    def test_daily_five_years_is_one_request(self, downloader, mock_session):
        mock_session.get.return_value = _api_resp([_daily_candle("2024-01-02")])
        downloader.fetch(408065, "2020-01-01", "2024-12-31", Interval.DAY)
        assert mock_session.get.call_count == 1

    def test_all_windows_succeed(self, downloader, mock_session):
        self._serve(mock_session, {})
        df = downloader.fetch(*self._ARGS)
        assert len(df) == 3
        assert mock_session.get.call_count == 3

    def test_failed_window_is_retried_once(self, downloader, mock_session):
        self._serve(mock_session, {"2024-03-01": 1})
        df = downloader.fetch(*self._ARGS)
        assert len(df) == 3

    def test_persistent_failure_raises_partial_data_error(self, downloader, mock_session):
        self._serve(mock_session, {"2024-03-01": 2})
        with pytest.raises(PartialDataError) as exc_info:
            downloader.fetch(*self._ARGS)
        err = exc_info.value
        assert err.failed_ranges == [(date(2024, 3, 1), date(2024, 4, 29))]
        assert len(err.partial_data) == 2
        assert "2024-03-01" in str(err)

    def test_partial_data_error_is_a_data_fetch_error(self):
        assert issubclass(PartialDataError, DataFetchError)

    def test_all_windows_failing_raises_plain_error(self, downloader, mock_session):
        mock_session.get.return_value = _http_error_resp(500)
        with pytest.raises(DataFetchError, match="HTTP 500") as exc_info:
            downloader.fetch(*self._ARGS)
        assert not isinstance(exc_info.value, PartialDataError)

    def test_http_403_mentions_expired_session(self, downloader, mock_session):
        mock_session.get.return_value = _http_error_resp(403)
        with pytest.raises(DataFetchError, match="expired"):
            downloader.fetch(*self._ARGS)

    def test_progress_reports_every_window(self, downloader, mock_session):
        self._serve(mock_session, {})
        calls = []
        downloader.fetch(*self._ARGS, progress_callback=lambda done, total: calls.append((done, total)))
        assert calls == [(1, 3), (2, 3), (3, 3)]


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
