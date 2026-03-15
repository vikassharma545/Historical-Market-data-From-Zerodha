"""Historical OHLCV candle downloader.

The downloader splits a date range into calendar-month windows and fetches
each window in parallel using a thread pool.  This matches the Zerodha API's
natural pagination unit and dramatically speeds up long historical downloads.

Design decisions
----------------
* Month windows are computed from the *exact* start/end dates, not from the
  1st of the month.  The original code always started from the 1st and then
  filtered; this approach requests only the data we actually need.
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Generator, List, Optional, Tuple

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


def _expected_cols(oi: bool) -> List[str]:
    return _OI_COLS if oi else _BASE_COLS


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

    # ---------------------------------------------------------------- public

    def fetch(
        self,
        instrument_token: int,
        start_date: str,
        end_date: str,
        interval: Interval,
        oi: bool = False,
    ) -> pd.DataFrame:
        """Download candles for *instrument_token* over [start_date, end_date].

        The date range is split into calendar-month windows and fetched
        in parallel (up to ``config.max_workers`` threads).

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
        """
        from_dt = pd.to_datetime(start_date).normalize()
        to_dt   = pd.to_datetime(end_date).normalize()

        if from_dt > to_dt:
            raise ValueError(
                f"start_date '{start_date}' must not be after end_date '{end_date}'"
            )

        # Resolve symbol once — avoids a linear DataFrame scan per month window.
        symbol = self._instruments.get_symbol(instrument_token)
        windows = list(_month_windows(from_dt, to_dt))

        logger.info(
            "Fetching %s | %s → %s | interval=%s | %d window(s)",
            symbol, from_dt.date(), to_dt.date(), interval.value, len(windows),
        )

        frames = self._fetch_all(instrument_token, windows, interval, oi, symbol)

        if not frames:
            logger.warning("No data returned for %s %s→%s", symbol, from_dt.date(), to_dt.date())
            return pd.DataFrame(columns=["tradingsymbol"] + _expected_cols(oi))

        df = pd.concat(frames, ignore_index=True)
        df = _clean(df, from_dt, to_dt)

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
    ) -> List[pd.DataFrame]:
        """Fetch all windows, in parallel when there are multiple."""
        if len(windows) == 1:
            # Single window — let errors propagate to the caller.
            df = self._fetch_window(token, *windows[0], interval, oi, symbol)
            return [df] if not df.empty else []

        # Pre-allocate result slots to preserve chronological order after
        # out-of-order parallel completion.
        results: List[Optional[pd.DataFrame]] = [None] * len(windows)
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as pool:
            future_to_idx = {
                pool.submit(self._fetch_window, token, s, e, interval, oi, symbol): i
                for i, (s, e) in enumerate(windows)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except DataFetchError as exc:
                    logger.error("Window %d failed: %s", idx, exc)
                    results[idx] = pd.DataFrame()

        return [r for r in results if r is not None and not r.empty]

    def _fetch_window(
        self,
        token: int,
        from_dt: pd.Timestamp,
        to_dt: pd.Timestamp,
        interval: Interval,
        oi: bool,
        symbol: str,
    ) -> pd.DataFrame:
        """Fetch one calendar-month (or partial) window from the Kite API."""
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

        try:
            resp = self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self._config.request_timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
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


def _month_windows(
    from_dt: pd.Timestamp, to_dt: pd.Timestamp
) -> Generator[Tuple[pd.Timestamp, pd.Timestamp], None, None]:
    """Yield ``(window_start, window_end)`` pairs, one per calendar month.

    The first window starts at *from_dt* (not the 1st of the month) and the
    last window ends at *to_dt*, so we never request more data than needed.

    Example::

        _month_windows("2024-01-15", "2024-03-10")
        → (2024-01-15, 2024-01-31)
        → (2024-02-01, 2024-02-29)
        → (2024-03-01, 2024-03-10)
    """
    current = from_dt
    while current <= to_dt:
        # End of the current calendar month
        month_end = current + pd.offsets.MonthEnd(0)
        # Clip to the actual requested end date
        window_end = min(month_end, to_dt)
        yield current, window_end
        # Start of the next month
        current = (month_end + pd.Timedelta(days=1)).normalize()
