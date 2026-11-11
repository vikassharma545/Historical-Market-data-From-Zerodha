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

def _json_resp(payload, status_code: int = 200):
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.json.return_value = payload
    return r


def _api_resp(candles: list):
    """A successful Kite-style candle payload."""
    return _json_resp({"status": "success", "data": {"candles": candles}})


def _error_resp(message: str = "Something went wrong", error_type: str = "GeneralException",
                status_code: int = 500):
    """Kite's error shape: ``{"status": "error", "message": …, "error_type": …}``."""
    return _json_resp(
        {"status": "error", "message": message, "error_type": error_type}, status_code
    )


def _not_json_resp():
    r = MagicMock(spec=requests.Response)
    r.status_code = 502
    r.json.side_effect = requests.JSONDecodeError("Expecting value", "<html>", 0)
    return r


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr("pyzdata.downloader.random.uniform", lambda a, b: 0)


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

    def test_invalid_date_range_raises(self, downloader):
        with pytest.raises(ValueError, match="must not be after"):
            downloader.fetch(408065, "2024-01-31", "2024-01-01", Interval.DAY)

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



# ---------------------------------------------------------------------------
# Retry rule: everything is retried until it succeeds — except a logout
# ---------------------------------------------------------------------------

_FAILURES = {
    "network error":      lambda: requests.ConnectionError("connection reset"),
    "timeout":            lambda: requests.Timeout("read timed out"),
    "not JSON":           _not_json_resp,
    "too many requests":  lambda: _error_resp("Too many requests", "NetworkException", 429),
    "other API error":    lambda: _error_resp("Something went wrong", "GeneralException", 500),
    "rejected request":   lambda: _error_resp("invalid from date", "InputException", 400),
    "no data":            lambda: _json_resp({"status": "success", "data": None}),
    "wrong column count": lambda: _api_resp([["2024-01-02T09:15:00+0530", 1, 2, 3]]),
}


class TestRetry:

    @pytest.mark.parametrize("failure", _FAILURES.values(), ids=_FAILURES.keys())
    def test_failure_is_retried_until_it_succeeds(
        self, downloader, mock_session, sample_candles, failure
    ):
        mock_session.get.side_effect = [failure(), failure(), failure(), _api_resp(sample_candles)]
        df = downloader.fetch(408065, "2024-01-02", "2024-01-02", Interval.MINUTE_1)
        assert len(df) == len(sample_candles)
        assert mock_session.get.call_count == 4

    def test_logout_stops_the_download_at_once(self, downloader, mock_session):
        mock_session.get.return_value = _error_resp(
            "Incorrect `api_key` or `access_token`.", "TokenException", 403
        )
        with pytest.raises(DataFetchError, match="logged you out"):
            downloader.fetch(*TestFetchMultiWindow._ARGS)  # three windows
        assert mock_session.get.call_count == 1  # no retry, later windows never start

    def test_close_cancels_a_download_that_is_still_retrying(self, downloader, mock_session):
        def _get(*args, **kwargs):
            downloader.close()  # as the web app's Log out does, from another thread
            raise requests.ConnectionError("down")

        mock_session.get.side_effect = _get
        with pytest.raises(DataFetchError, match="cancelled"):
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
                return _error_resp()
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

    def test_failing_window_is_retried_until_it_succeeds(self, downloader, mock_session):
        self._serve(mock_session, {"2024-03-01": 5})
        df = downloader.fetch(*self._ARGS)
        assert len(df) == 3  # no gap
        assert mock_session.get.call_count == 3 + 5

    def test_partial_data_error_is_still_importable_as_a_data_fetch_error(self):
        assert issubclass(PartialDataError, DataFetchError)

    def test_logout_message_says_the_session_expired(self, downloader, mock_session):
        # The web app keys its "log in again" message on the word "expired".
        mock_session.get.return_value = _error_resp("Session expired", "TokenException", 403)
        with pytest.raises(DataFetchError, match="session has expired"):
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
