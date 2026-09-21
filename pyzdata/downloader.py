"""Historical OHLCV candle downloader.

The downloader splits a date range into the largest windows the Kite API
accepts for the requested interval and fetches them in parallel using a
thread pool.  Daily candles fit ~5 years into one request; 1-minute candles
need one request per 60 days.

Design decisions
----------------
* Window size depends on the interval (see ``_max_days``).  Earlier versions
  always used calendar months, which cost 60 requests for 5 years of daily
  data where a single request is enough.
* A failed window is never dropped silently.  It is retried once; if it
  still fails the caller gets a :class:`~pyzdata.exceptions.PartialDataError`
  that names the missing ranges and carries the rows that did download.
* Timezone handling: Zerodha returns IST timestamps (``+05:30`` suffix).
  We parse them as UTC-aware, convert to IST, then strip the tz-info to
  produce naive IST timestamps — consistent with how most Indian trading
  applications store candle data.
* Column count is validated *before* assigning names.  The original code did
  ``data.columns = columns`` without checking width, which silently
  misassigned columns if the API response shape changed.
* Deduplication uses ``subset=["datetime"]`` so only the first occurrence of
  each timestamp is kept.  The original code deduped across all columns,
  which could retain two rows for the same candle if any numeric value differed
  slightly (floating-point jitter).
* ``_fetch_all`` returns results in *window order*, not completion order, so
  the final ``pd.concat`` is always chronological.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Callable, Dict, Generator, List, Optional, Tuple

import pandas as pd
import requests

from .config import Config
from .exceptions import DataFetchError, PartialDataError
from .instruments import InstrumentManager
from .models import Interval

logger = logging.getLogger(__name__)

# Column definitions — must match Zerodha API response order exactly.
_BASE_COLS: List[str] = ["datetime", "open", "high", "low", "close", "volume"]
_OI_COLS:   List[str] = _BASE_COLS + ["open_interest"]

_IST_TZ = "Asia/Kolkata"

# Largest date span (in days) the Kite API serves in a single request.
_MAX_DAYS_PER_REQUEST: Dict[Interval, int] = {
    Interval.MINUTE_1:  60,
    Interval.MINUTE_2:  60,
    Interval.MINUTE_3:  60,
    Interval.MINUTE_4:  60,
    Interval.MINUTE_5:  100,
    Interval.MINUTE_10: 100,
    Interval.MINUTE_15: 200,
    Interval.MINUTE_30: 200,
    Interval.HOUR_1:    400,
    Interval.HOUR_2:    400,
    Interval.HOUR_3:    400,
    Interval.HOUR_4:    400,
    Interval.DAY:       2000,
}


def _max_days(interval: Interval) -> int:
    # Unknown intervals get the smallest window — slower, but always accepted.
    return _MAX_DAYS_PER_REQUEST.get(interval, 60)


def _expected_cols(oi: bool) -> List[str]:
    return _OI_COLS if oi else _BASE_COLS


class _Throttle:
    """Thread-safe rate limiter that enforces a minimum gap between calls."""

    def __init__(self, max_per_second: float) -> None:
        self._min_interval = 1.0 / max_per_second if max_per_second > 0 else 0.0
        self._lock = Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


class DataDownloader:
    """Downloads OHLCV (and optional OI) candles from the Kite historical API."""

    _URL = "{root}/instruments/historical/{token}/{interval}"

    def __init__(
        self,
        session: requests.Session,
        auth_headers: Dict[str, str],
        instruments: InstrumentManager,
        config: Config,
    ) -> None:
        self._session = session
        self._headers = auth_headers
        self._instruments = instruments
        self._config = config
        self._throttle = _Throttle(config.rate_limit_per_second)

    # ---------------------------------------------------------------- public

    def fetch(
        self,
        instrument_token: int,
        start_date: str,
        end_date: str,
        interval: Interval,
        oi: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> pd.DataFrame:
        """Download candles for *instrument_token* over [start_date, end_date].

        The date range is split into the largest windows the API allows for
        *interval* and fetched in parallel (up to ``config.max_workers``
        threads).

        Parameters
        ----------
        instrument_token:
            Zerodha numeric instrument token.
        start_date, end_date:
            Any string parseable by ``pd.to_datetime`` (e.g. ``"2024-01-01"``).
        interval:
            :class:`~pyzdata.models.Interval` candle granularity.
        oi:
            When ``True``, include an ``open_interest`` column.

        Returns
        -------
        pd.DataFrame
            Columns: ``tradingsymbol, datetime, open, high, low, close, volume``
            (plus ``open_interest`` when *oi=True*).
            Sorted by ``datetime``, no duplicate timestamps.

        Raises
        ------
        ValueError
            If ``start_date > end_date``.
        DataFetchError
            On HTTP or API-level failures.
        PartialDataError
            When only some date ranges failed.  ``exc.partial_data`` holds
            the rows that were fetched, ``exc.failed_ranges`` the gaps.
        """
        from_dt =pd.to_datetime(start_date).normalize()
        to_dt   = pd.to_datetime(end_date).normalize()

        if from_dt > to_dt:
            raise ValueError(
                f"start_date '{start_date}' must not be after end_date '{end_date}'"
            )

        # Resolve symbol once — avoids a linear DataFrame scan per window.
        symbol = self._instruments.get_symbol(instrument_token)
        windows = list(_date_windows(from_dt, to_dt, _max_days(interval)))

        logger.info(
            "Fetching %s | %s → %s | interval=%s | %d window(s)",
            symbol, from_dt.date(), to_dt.date(), interval.value, len(windows),
        )

        frames, failed = self._fetch_all(
            instrument_token, windows, interval, oi, symbol, progress_callback
        )

        if frames:
            df = _clean(pd.concat(frames, ignore_index=True), from_dt, to_dt)
        else:
            df = pd.DataFrame(columns=["tradingsymbol"] + _expected_cols(oi))

        if failed:
            failed_ranges = [(s.date(), e.date()) for s, e in failed]
            missing = ", ".join(f"{s} → {e}" for s, e in failed_ranges)
            raise PartialDataError(
                f"{len(failed)} of {len(windows)} date ranges failed for {symbol}: {missing}",
                partial_data=df,
                failed_ranges=failed_ranges,
            )

        if df.empty:
            logger.warning("No data returned for %s %s→%s", symbol, from_dt.date(), to_dt.date())
        else:
            logger.info("Fetched %d rows for %s", len(df), symbol)
        return df

    # -------------------------------------------------------------- private

    def _fetch_all(
        self,
        token: int,
        windows: List[Tuple[pd.Timestamp, pd.Timestamp]],
        interval: Interval,
        oi: bool,
        symbol: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[pd.DataFrame], List[Tuple[pd.Timestamp, pd.Timestamp]]]:
        """Fetch all windows in parallel and return ``(frames, failed_windows)``.

        Raises the first :class:`DataFetchError` when *every* window failed —
        that is an outage or an expired session, not a gap in the data.
        """
        # Pre-allocate result slots to preserve chronological order after
        # out-of-order parallel completion.
        results: List[Optional[pd.DataFrame]] = [None] * len(windows)
        errors: Dict[int, DataFetchError] = {}
        completed = 0

        with ThreadPoolExecutor(max_workers=self._config.max_workers) as pool:
            future_to_idx = {
                pool.submit(self._fetch_window, token, s, e, interval, oi, symbol): i
                for i, (s, e) in enumerate(windows)
            }
            # Results are consumed on this thread only, so the progress
            # callback never runs concurrently.
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except DataFetchError as exc:
                    logger.warning("Window %d failed, will retry: %s", idx, exc)
                    errors[idx] = exc

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(windows))

        if len(errors) == len(windows):
            raise errors[min(errors)]

        for idx in sorted(errors):
            try:
                results[idx] = self._fetch_window(token, *windows[idx], interval, oi, symbol)
                del errors[idx]
            except DataFetchError as exc:
                logger.error("Window %d failed again: %s", idx, exc)

        frames = [r for r in results if r is not None and not r.empty]
        return frames, [windows[i] for i in sorted(errors)]

    def _fetch_window(
        self,
        token: int,
        from_dt: pd.Timestamp,
        to_dt: pd.Timestamp,
        interval: Interval,
        oi: bool,
        symbol: str,
    ) -> pd.DataFrame:
        """Fetch one date window from the Kite API."""
        url = self._URL.format(
            root=self._config.root_url, token=token, interval=interval.value
        )
        params = {
            # Use end-of-day as the "to" time so the last day is always included.
            "from": from_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "to":   to_dt.strftime("%Y-%m-%d 23:59:59"),
            "oi":   int(oi),
        }
        logger.debug("GET %s | from=%s to=%s", url, params["from"], params["to"])

        self._throttle.wait()
        try:
            resp = self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self._config.request_timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response.status_code in (401, 403):
                raise DataFetchError(
                    f"HTTP {exc.response.status_code} fetching {symbol}: your Zerodha "
                    "session has expired or the enctoken is invalid. Log in again."
                ) from exc
            raise DataFetchError(
                f"HTTP {exc.response.status_code} fetching {symbol} "
                f"({from_dt.date()} → {to_dt.date()})"
            ) from exc
        except requests.RequestException as exc:
            raise DataFetchError(
                f"Network error fetching {symbol}: {exc}"
            ) from exc

        payload = resp.json()
        if payload.get("status") != "success":
            raise DataFetchError(
                f"API error for {symbol}: {payload.get('message', 'unknown error')}"
            )

        candles = payload.get("data", {}).get("candles", [])
        if not candles:
            logger.debug(
                "No candles for %s %s→%s", symbol, from_dt.date(), to_dt.date()
            )
            return pd.DataFrame()

        cols = _expected_cols(oi)

        # Validate column count before assignment to prevent silent misalignment.
        actual_width = len(candles[0])
        if actual_width != len(cols):
            raise DataFetchError(
                f"Unexpected column count from Kite API: got {actual_width}, "
                f"expected {len(cols)}. "
                f"Check whether the 'oi' parameter matches the instrument type."
            )

        df = pd.DataFrame(candles, columns=cols)
        df = _parse_datetime(df)
        df["tradingsymbol"] = symbol

        # Re-order: tradingsymbol first, then the rest.
        df = df[["tradingsymbol"] + cols]

        logger.debug(
            "%d rows for %s %s→%s", len(df), symbol, from_dt.date(), to_dt.date()
        )
        return df


# ---------------------------------------------------------------------------
# Module-level pure helpers (easily unit-testable without a class instance)
# ---------------------------------------------------------------------------

def _parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the datetime column and normalise to naive IST timestamps.

    Zerodha returns ISO-8601 strings with a ``+05:30`` suffix.  We convert
    to IST and then strip the tz-info so downstream code works with simple
    naive timestamps — consistent with most Indian trading applications.
    """
    dt = pd.to_datetime(df["datetime"], utc=False)
    if dt.dt.tz is not None:
        dt = dt.dt.tz_convert(_IST_TZ).dt.tz_localize(None)
    df = df.copy()
    df["datetime"] = dt
    return df


def _clean(df: pd.DataFrame, from_dt: pd.Timestamp, to_dt: pd.Timestamp) -> pd.DataFrame:
    """Deduplicate on timestamp, clip to exact range, and sort."""
    # Dedup on datetime only — protects against floating-point jitter that
    # would cause two rows for the same candle to survive an all-columns dedup.
    df = df.drop_duplicates(subset=["datetime"])
    date_col = df["datetime"].dt.date
    df = df[(date_col >= from_dt.date()) & (date_col <= to_dt.date())]
    return df.sort_values("datetime").reset_index(drop=True)


def _date_windows(
    from_dt: pd.Timestamp, to_dt: pd.Timestamp, max_days: int
) -> Generator[Tuple[pd.Timestamp, pd.Timestamp], None, None]:
    """Yield ``(window_start, window_end)`` pairs of at most *max_days* days.

    Windows are contiguous and non-overlapping; the last one ends at *to_dt*.

    Example::

        _date_windows("2024-01-01", "2024-05-31", max_days=60)
        -> (2024-01-01, 2024-02-29)
        -> (2024-03-01, 2024-04-29)
        -> (2024-04-30, 2024-05-31)
    """
    current = from_dt
    while current <= to_dt:
        window_end = min(current + pd.Timedelta(days=max_days - 1), to_dt)
        yield current, window_end
        current = window_end + pd.Timedelta(days=1)
