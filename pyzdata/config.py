"""Runtime configuration for PyZData.

All fields can be overridden through environment variables prefixed with
``PYZDATA_`` (see :meth:`Config.from_env`).  This makes it trivial to tune
behaviour in CI/CD or production without touching source code.

Example .env::

    PYZDATA_MAX_RETRIES=3
    PYZDATA_MAX_WORKERS=8
    PYZDATA_CACHE_TTL_HOURS=12
    PYZDATA_LOG_LEVEL=DEBUG
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Config:
    """Immutable-by-convention configuration container.

    Instantiate directly for full control, or call :meth:`from_env` to pick
    up overrides from environment variables.
    """

    # ------------------------------------------------------------------ URLs
    root_url: str = "https://kite.zerodha.com/oms"
    login_url: str = "https://kite.zerodha.com/api/login"
    twofa_url: str = "https://kite.zerodha.com/api/twofa"
    instruments_url: str = "https://api.kite.trade/instruments"

    # --------------------------------------------------------- Retry / HTTP
    #: Total retry attempts for transient HTTP failures.
    max_retries: int = 5
    #: Exponential backoff factor (seconds).  With factor=1 the delays are
    #: 0s, 2s, 4s, 8s, 16s between consecutive retries.
    backoff_factor: float = 1.0
    #: HTTP status codes that should trigger a retry.
    retry_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)
    #: Seconds before a request is considered timed-out.
    request_timeout: int = 30

    # ------------------------------------------------------------ Caching
    #: Hours a cached instruments CSV is considered fresh.  Set to 0 to
    #: always re-download (useful for testing).
    instruments_cache_ttl_hours: float = 24.0
    #: Absolute path for the instruments cache file.  ``None`` uses the
    #: platform default: ``~/.pyzdata/instruments.csv``.
    instruments_cache_path: Optional[str] = None

    # --------------------------------------------------- Parallel downloads
    #: Maximum worker threads for concurrent monthly fetches.
    max_workers: int = 4

    # ----------------------------------------------------------------- Log
    #: Python logging level name for the ``pyzdata`` logger hierarchy.
    log_level: str = "WARNING"

    # ---------------------------------------------------------------- factory

    @classmethod
    def from_env(cls) -> Config:
        """Build a :class:`Config` from ``PYZDATA_*`` environment variables.

        Any variable not set in the environment falls back to the dataclass
        default.  Example::

            export PYZDATA_MAX_WORKERS=8
            export PYZDATA_LOG_LEVEL=DEBUG
        """
        return cls(
            max_retries=int(os.getenv("PYZDATA_MAX_RETRIES", 5)),
            backoff_factor=float(os.getenv("PYZDATA_BACKOFF_FACTOR", 1.0)),
            request_timeout=int(os.getenv("PYZDATA_TIMEOUT", 30)),
            max_workers=int(os.getenv("PYZDATA_MAX_WORKERS", 4)),
            instruments_cache_path=os.getenv("PYZDATA_CACHE_PATH") or None,
            instruments_cache_ttl_hours=float(
                os.getenv("PYZDATA_CACHE_TTL_HOURS", 24.0)
            ),
            log_level=os.getenv("PYZDATA_LOG_LEVEL", "WARNING").upper(),
        )
