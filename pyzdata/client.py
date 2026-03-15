"""PyZData public client — the single entry point for library users.

``PyZData`` is a thin facade that wires together the four specialised
components (:mod:`auth`, :mod:`instruments`, :mod:`downloader`, :mod:`config`)
and exposes a clean, stable public API.

Facade pattern rationale
------------------------
The original ``pyzdata.py`` was a God class that mixed authentication,
instrument resolution, HTTP session management, data downloading, and
DataFrame processing in a single 171-line class.  Splitting those concerns
makes each component independently testable and makes the overall data flow
easier to reason about.

This ``client.py`` module is intentionally thin: it only constructs
dependencies and delegates to them.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import KiteAuth
from .config import Config
from .downloader import DataDownloader
from .exceptions import ConfigurationError
from .instruments import InstrumentManager
from .models import Interval

logger = logging.getLogger(__name__)


class PyZData:
    """High-level client for downloading historical OHLCV data from Zerodha.

    Authentication
    --------------
    Pass **either** an ``enctoken`` **or** the credential triple
    (``user_id``, ``password``, ``totp``):

    .. code-block:: python

        from pyzdata import PyZData, Interval

        # Option A — full credential login (also handles 2FA)
        client = PyZData(user_id="AB1234", password="secret", totp="123456")

        # Option B — pre-obtained enctoken (faster, no login round-trip)
        client = PyZData(enctoken="<your_enctoken>")

    Configuration
    -------------
    A :class:`~pyzdata.config.Config` instance can be passed to override
    any default; otherwise :meth:`Config.from_env` is called automatically
    (which reads ``PYZDATA_*`` environment variables):

    .. code-block:: python

        from pyzdata import Config, PyZData

        cfg = Config(max_workers=8, log_level="DEBUG")
        client = PyZData(enctoken="...", config=cfg)

    Logging
    -------
    All internal log messages are emitted under the ``pyzdata`` logger
    hierarchy.  To enable verbose output add before constructing the client:

    .. code-block:: python

        import logging
        logging.basicConfig(level=logging.DEBUG)

    Migration from v0.1
    -------------------
    * Remove the ``print_logs=True`` parameter — use the logging system instead.
    * ``totp`` now accepts both ``str`` and ``int`` (leading zeros are safe).
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        totp: Optional[Union[str, int]] = None,
        enctoken: Optional[str] = None,
        config: Optional[Config] = None,
    ) -> None:
        self._config = config or Config.from_env()
        _configure_library_logging(self._config.log_level)

        self._session = _build_session(self._config)
        authenticator = KiteAuth(self._session, self._config)

        if enctoken is not None:
            _token = enctoken
            logger.info("Using pre-supplied enctoken.")
        elif user_id is not None and password is not None and totp is not None:
            _token = authenticator.login_with_credentials(
                user_id, password, str(totp)
            )
        else:
            raise ConfigurationError(
                "Provide either 'enctoken' or all three of "
                "('user_id', 'password', 'totp')."
            )

        self._auth_headers = KiteAuth.make_auth_headers(_token)

        self._instruments = InstrumentManager(self._session, self._config)
        self._instruments.load()

        self._downloader = DataDownloader(
            self._session,
            self._auth_headers,
            self._instruments,
            self._config,
        )

    # ---------------------------------------------------------------- public

    def get_instrument_token(self, tradingsymbol: str, exchange: str) -> int:
        """Resolve a *tradingsymbol* + *exchange* pair to an instrument token.

        Parameters
        ----------
        tradingsymbol:
            Exact Zerodha symbol string, e.g. ``"NIFTY 50"`` or ``"RELIANCE"``.
        exchange:
            Exchange code: ``"NSE"``, ``"BSE"``, ``"NFO"``, ``"MCX"``, etc.

        Returns
        -------
        int
            Numeric ``instrument_token`` for use with :meth:`get_data`.

        Raises
        ------
        InstrumentNotFoundError
            When no matching instrument is found.  Call
            :meth:`search_instruments` to discover the correct symbol name.
        """
        return self._instruments.get_token(tradingsymbol, exchange)

    def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> pd.DataFrame:
        """Return instruments whose symbol contains *query* (case-insensitive).

        Useful for discovering the exact symbol string required by
        :meth:`get_instrument_token`.

        Parameters
        ----------
        query:
            Partial symbol string, e.g. ``"NIFTY"`` or ``"RELI"``.
        exchange:
            Optionally filter results to a single exchange.

        Returns
        -------
        pd.DataFrame
            Matching rows from the Zerodha instruments master.
        """
        return self._instruments.search(query, exchange)

    def get_data(
        self,
        instrument_token: int,
        start_date: str,
        end_date: str,
        interval: Interval,
        oi: bool = False,
    ) -> pd.DataFrame:
        """Download historical candle data for one instrument.

        Parameters
        ----------
        instrument_token:
            Zerodha instrument token — obtain via :meth:`get_instrument_token`.
        start_date, end_date:
            Date strings in ``"YYYY-MM-DD"`` format (or any string accepted
            by ``pd.to_datetime``).
        interval:
            Candle granularity as a :class:`~pyzdata.models.Interval` member.
        oi:
            Set to ``True`` to include the ``open_interest`` column.
            Only meaningful for F&O instruments.

        Returns
        -------
        pd.DataFrame
            Columns: ``tradingsymbol, datetime, open, high, low, close, volume``
            (plus ``open_interest`` when *oi=True*).
            Sorted by ``datetime`` ascending, no duplicate timestamps.

        Raises
        ------
        ValueError
            When ``start_date > end_date``.
        DataFetchError
            On HTTP or API-level failures after all retries are exhausted.

        Example
        -------
        .. code-block:: python

            token = client.get_instrument_token("NIFTY 50", "NSE")
            df = client.get_data(
                token,
                start_date="2024-01-01",
                end_date="2024-12-31",
                interval=Interval.DAY,
            )
            print(df.head())
        """
        return self._downloader.fetch(
            instrument_token, start_date, end_date, interval, oi
        )


# ---------------------------------------------------------------------------
# Module-level helpers (not part of the public API)
# ---------------------------------------------------------------------------

def _build_session(config: Config) -> requests.Session:
    """Create a ``requests.Session`` with the configured retry strategy."""
    session = requests.Session()
    retry = Retry(
        total=config.max_retries,
        backoff_factor=config.backoff_factor,
        status_forcelist=list(config.retry_status_codes),
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _configure_library_logging(level: str) -> None:
    """Set the log level on the ``pyzdata`` logger.

    Only adds a ``StreamHandler`` if the ``pyzdata`` root logger has no
    handlers yet — this respects any logging configuration the application
    has already set up (i.e. we never override the host application's
    logging setup).
    """
    root = logging.getLogger("pyzdata")
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(handler)
    try:
        root.setLevel(level)
    except ValueError:
        root.setLevel(logging.WARNING)
        logger.warning("Unknown log level '%s', defaulting to WARNING.", level)
