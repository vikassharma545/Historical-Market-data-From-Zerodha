"""Historical OHLCV candle downloader.

The downloader splits a date range into the largest windows the Kite API
accepts for the requested interval and fetches them one after another.
Daily candles fit ~5 years into one request; 1-minute candles need one
request per 60 days.

Design decisions
----------------
* Window size depends on the interval (see ``_max_days``).  Earlier versions
  always used calendar months, which cost 60 requests for 5 years of daily
  data where a single request is enough.
* Every window is retried until it succeeds (see ``_fetch_window``).
  Network errors, timeouts, Kite API errors, "Too many requests" and
  garbled responses all pass, so the download waits (jittered) and tries
  again.  The one exception is a ``TokenException``: Zerodha has logged the
  account out, no retry can succeed, and the download stops with a
  :class:`~pyzdata.exceptions.DataFetchError`.
* Windows are fetched sequentially.  The rate limit (3 requests/s) is the
  real ceiling, and a plain loop keeps Ctrl-C and cancelling trivial.
* Timezone handling: Zerodha returns IST timestamps (``+05:30`` suffix).
  We convert to IST, then strip the tz-info to produce naive IST timestamps
  — consistent with how most Indian trading applications store candle data.
* Column count is validated *before* assigning names, so a change in the
  API's response shape fails loudly instead of misassigning columns.
* Deduplication uses ``subset=["datetime"]`` so only the first occurrence of
  each timestamp is kept, regardless of floating-point jitter in the values.
"""

from __future__ import annotations

import logging
import random
import time
from threading import Lock
from typing import Callable, Dict, Generator, List, Optional, Tuple

import pandas as pd
import requests

from .config import Config
from .exceptions import DataFetchError
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
        self._closed = False

    def close(self) -> None:
        """Make a download that is still retrying give up (after its current wait)."""
        self._closed = True

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
        *interval*; each window is retried until it succeeds.

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
        progress_callback:
            Called as ``callback(done, total)`` after each window.

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
            Only when Zerodha logged the account out (``TokenException``) or
            :meth:`close` cancelled the download.  Every other failure is
            retried until it succeeds.
        """
        from_dt = pd.to_datetime(start_date).normalize()
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

        frames = []
        for done, (start, end) in enumerate(windows, start=1):
            frame = self._fetch_window(instrument_token, start, end, interval, oi, symbol)
            if not frame.empty:
                frames.append(frame)
            if progress_callback:
                progress_callback(done, len(windows))

        if frames:
            df = _clean(pd.concat(frames, ignore_index=True), from_dt, to_dt)
        else:
            df = pd.DataFrame(columns=["tradingsymbol"] + _expected_cols(oi))

        if df.empty:
            logger.warning("No data returned for %s %s→%s", symbol, from_dt.date(), to_dt.date())
        else:
            logger.info("Fetched %d rows for %s", len(df), symbol)
        return df

    # -------------------------------------------------------------- private

    def _fetch_window(
        self,
        token: int,
        from_dt: pd.Timestamp,
        to_dt: pd.Timestamp,
        interval: Interval,
        oi: bool,
        symbol: str,
    ) -> pd.DataFrame:
        """Fetch one date window, retrying every failure except a logout.

        * ``TokenException``  → stop: the account is logged out.
        * "Too many requests" → wait 0.5–3 s, retry.
        * other Kite error    → warn, wait 1–5 s, retry.
        * any exception       → warn, wait 1 s up to 15 s (grows per attempt), retry.
        """
        url = self._URL.format(
            root=self._config.root_url, token=token, interval=interval.value
        )
        params = {
            # Use end-of-day as the "to" time so the last day is always included.
            "from": from_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "to":   to_dt.strftime("%Y-%m-%d 23:59:59"),
            "oi":   int(oi),
        }
        span = f"{from_dt.date()} → {to_dt.date()}"

        attempt = 0
        while True:
            attempt += 1
            try:
                logger.debug("GET %s | from=%s to=%s", url, params["from"], params["to"])
                self._throttle.wait()
                resp = self._session.get(
                    url,
                    params=params,
                    headers=self._headers,
                    timeout=self._config.request_timeout,
                )
                response = resp.json()  # Kite answers in JSON, errors included

                if response.get("status") == "error":
                    msg = response.get("message", "")
                    if response.get("error_type") == "TokenException":
                        # The account was logged out: no retry can succeed.
                        raise DataFetchError(
                            f"Zerodha logged you out while fetching {symbol}: your session "
                            f"has expired ({msg or 'TokenException'}). Log in again."
                        )
                    if msg == "Too many requests":
                        delay = random.uniform(0.5, 3)
                    else:
                        logger.warning("API error for %s %s (attempt %d): %s",
                                       symbol, span, attempt, msg)
                        delay = random.uniform(1, 5)
                else:
                    return _to_frame(response["data"]["candles"], oi, symbol, span)

            except DataFetchError:
                raise  # logged out — see above
            except Exception as exc:  # network, timeout, not JSON, garbled candles …
                logger.warning("Fetch error for %s %s (attempt %d): %s",
                               symbol, span, attempt, exc)
                delay = random.uniform(1, min(3 * attempt, 15))

            time.sleep(delay)  # time.sleep, not Event.wait: Ctrl-C must work on Windows
            if self._closed:
                raise DataFetchError(f"Download of {symbol} cancelled")


# ---------------------------------------------------------------------------
# Module-level pure helpers (easily unit-testable without a class instance)
# ---------------------------------------------------------------------------

def _to_frame(candles: list, oi: bool, symbol: str, span: str) -> pd.DataFrame:
    """Turn one window's raw candles into a frame: ``tradingsymbol`` first."""
    if not candles:
        logger.debug("No candles for %s %s", symbol, span)
        return pd.DataFrame()

    cols = _expected_cols(oi)
    # Validate column count before assignment to prevent silent misalignment.
    actual_width = len(candles[0])
    if actual_width != len(cols):
        raise ValueError(
            f"Unexpected column count from Kite API: got {actual_width}, "
            f"expected {len(cols)}. "
            f"Check whether the 'oi' parameter matches the instrument type."
        )

    df = _parse_datetime(pd.DataFrame(candles, columns=cols))
    df["tradingsymbol"] = symbol
    logger.debug("%d rows for %s %s", len(df), symbol, span)
    return df[["tradingsymbol"] + cols]


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
