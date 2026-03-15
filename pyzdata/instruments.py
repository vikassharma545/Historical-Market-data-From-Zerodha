"""Zerodha instruments master management with transparent disk caching.

The instruments CSV (≈50 MB, ~10 k rows) is downloaded once and cached at
``~/.pyzdata/instruments.csv`` (or a user-specified path).  On subsequent
runs the cached file is reused until it exceeds ``config.instruments_cache_ttl_hours``
(default 24 h), avoiding a slow network download on every script execution.

Design decisions
----------------
* Caching is opt-in-by-default: the default cache path is inside the user's
  home directory so it is never accidentally committed to source control.
* ``load()`` is separated from ``__init__`` so the manager can be constructed
  and injected without triggering I/O at instantiation time (useful in tests).
* ``search()`` exposes partial-match symbol lookup so users can discover
  instrument tokens without knowing the exact symbol string.
"""

from __future__ import annotations

import logging
import time
from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from .config import Config
from .exceptions import InstrumentNotFoundError

logger = logging.getLogger(__name__)

_TOKEN_COL    = "instrument_token"
_SYMBOL_COL   = "tradingsymbol"
_EXCHANGE_COL = "exchange"


class InstrumentManager:
    """Loads and queries the Zerodha instruments master CSV."""

    def __init__(self, session: requests.Session, config: Config) -> None:
        self._session = session
        self._config = config
        self._df: Optional[pd.DataFrame] = None

    # ---------------------------------------------------------------- public

    def load(self) -> None:
        """Load instruments data, using a fresh disk cache when available.

        Call this once after construction.  :class:`PyZData` calls it
        automatically during ``__init__``.
        """
        cache_path = self._cache_path()
        if cache_path and self._is_cache_fresh(cache_path):
            logger.info("Instruments loaded from cache: %s", cache_path)
            self._df = pd.read_csv(cache_path, low_memory=False)
        else:
            self._df = self._download()
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                self._df.to_csv(cache_path, index=False)
                logger.debug("Instruments cached to %s", cache_path)

    def get_token(self, tradingsymbol: str, exchange: str) -> int:
        """Return the ``instrument_token`` for a symbol + exchange pair.

        Raises
        ------
        InstrumentNotFoundError
            When the symbol/exchange combination does not exist.
        """
        self._require_loaded()
        mask = (
            (self._df[_SYMBOL_COL] == tradingsymbol)
            & (self._df[_EXCHANGE_COL] == exchange)
        )
        result = self._df[mask]
        if result.empty:
            raise InstrumentNotFoundError(
                f"No instrument found: symbol='{tradingsymbol}' exchange='{exchange}'. "
                f"Try client.search_instruments('{tradingsymbol}') to find the correct symbol."
            )
        return int(result.iloc[0][_TOKEN_COL])

    def get_symbol(self, instrument_token: int) -> str:
        """Return the ``tradingsymbol`` for a given ``instrument_token``.

        Raises
        ------
        InstrumentNotFoundError
            When no instrument matches the token.
        """
        self._require_loaded()
        result = self._df[self._df[_TOKEN_COL] == instrument_token]
        if result.empty:
            raise InstrumentNotFoundError(
                f"No instrument found with token={instrument_token}"
            )
        return str(result.iloc[0][_SYMBOL_COL])

    def search(self, query: str, exchange: Optional[str] = None) -> pd.DataFrame:
        """Case-insensitive substring search on the tradingsymbol column.

        Parameters
        ----------
        query:
            Partial symbol string, e.g. ``"NIFTY"`` or ``"RELI"``.
        exchange:
            Optionally filter to a single exchange (``"NSE"``, ``"NFO"``, etc.).

        Returns
        -------
        pd.DataFrame
            Matching rows from the instruments master, reset-indexed.
        """
        self._require_loaded()
        mask = self._df[_SYMBOL_COL].str.contains(
            query, case=False, na=False, regex=False
        )
        if exchange:
            mask &= self._df[_EXCHANGE_COL] == exchange
        return self._df[mask].reset_index(drop=True)

    # -------------------------------------------------------------- private

    def _download(self) -> pd.DataFrame:
        logger.info("Downloading instruments from %s", self._config.instruments_url)
        try:
            resp = self._session.get(
                self._config.instruments_url,
                timeout=self._config.request_timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to download instruments CSV: {exc}"
            ) from exc
        return pd.read_csv(StringIO(resp.text), low_memory=False)

    def _cache_path(self) -> Optional[Path]:
        if self._config.instruments_cache_path:
            return Path(self._config.instruments_cache_path)
        # Platform-default: ~/.pyzdata/instruments.csv
        return Path.home() / ".pyzdata" / "instruments.csv"

    def _is_cache_fresh(self, path: Path) -> bool:
        if not path.exists():
            return False
        if self._config.instruments_cache_ttl_hours <= 0:
            return False
        age_hours = (time.time() - path.stat().st_mtime) / 3600.0
        return age_hours < self._config.instruments_cache_ttl_hours

    def _require_loaded(self) -> None:
        if self._df is None:
            raise RuntimeError(
                "InstrumentManager not loaded. "
                "Call load() first, or use the PyZData client which loads automatically."
            )
