"""Runtime configuration for PyZData.

All fields can be overridden through environment variables prefixed with
``PYZDATA_`` (see :meth:`Config.from_env`).  This makes it trivial to tune
behaviour in CI/CD or production without touching source code.

Example .env::

    PYZDATA_MAX_RETRIES=3
    PYZDATA_CACHE_TTL_HOURS=12
    PYZDATA_LOG_LEVEL=DEBUG
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from .exceptions import ConfigurationError


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
    #: Cheap authenticated endpoint used to check that an enctoken is valid.
    profile_url: str = "https://kite.zerodha.com/oms/user/profile"
    instruments_url: str = "https://api.kite.trade/instruments"

    # --------------------------------------------------------- Retry / HTTP
    #: Quick retries per HTTP request for transient failures.  Candle
    #: downloads additionally keep retrying until they succeed.
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

    # ------------------------------------------------------------ Downloads
    #: Unused — date windows are fetched one at a time.  Kept so existing
    #: ``Config(max_workers=...)`` calls keep working.
    max_workers: int = 4
    #: Maximum API requests per second.  Zerodha's historical data endpoint
    #: typically allows ~3 req/s.  Set to ``0`` to disable throttling.
    rate_limit_per_second: float = 3.0

    # ----------------------------------------------------------------- Log
    #: Level for the ``pyzdata`` loggers, e.g. ``"DEBUG"``.  ``None`` leaves
    #: it to the application's own ``logging`` setup.
    log_level: Optional[str] = None

    def __post_init__(self) -> None:
        # A bad value here would otherwise surface as the same error on
        # every retry of a download that never ends.
        if self.request_timeout <= 0:
            raise ConfigurationError(f"request_timeout must be > 0, got {self.request_timeout}")
        if self.max_retries < 0:
            raise ConfigurationError(f"max_retries must be >= 0, got {self.max_retries}")

    # ---------------------------------------------------------------- factory

    @classmethod
    def from_env(cls) -> Config:
        """Build a :class:`Config` from ``PYZDATA_*`` environment variables.

        Any variable not set in the environment falls back to the dataclass
        default.  Example::

            export PYZDATA_RATE_LIMIT=2
            export PYZDATA_LOG_LEVEL=DEBUG
        """
        d = cls()  # defaults live in one place: the fields above
        return cls(
            max_retries=_env_int("PYZDATA_MAX_RETRIES", d.max_retries),
            backoff_factor=_env_float("PYZDATA_BACKOFF_FACTOR", d.backoff_factor),
            request_timeout=_env_int("PYZDATA_TIMEOUT", d.request_timeout),
            rate_limit_per_second=_env_float("PYZDATA_RATE_LIMIT", d.rate_limit_per_second),
            instruments_cache_path=os.getenv("PYZDATA_CACHE_PATH") or None,
            instruments_cache_ttl_hours=_env_float(
                "PYZDATA_CACHE_TTL_HOURS", d.instruments_cache_ttl_hours
            ),
            log_level=(os.getenv("PYZDATA_LOG_LEVEL") or "").upper() or None,
        )


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigurationError(
            f"Environment variable {name}={raw!r} is not a valid integer"
        )


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ConfigurationError(
            f"Environment variable {name}={raw!r} is not a valid number"
        )
