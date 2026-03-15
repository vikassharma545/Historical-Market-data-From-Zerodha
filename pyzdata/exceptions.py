"""Custom exception hierarchy for PyZData.

Callers can catch the base :class:`PyZDataError` for any library failure,
or individual subclasses for finer-grained handling:

    try:
        token = client.get_instrument_token("XYZ", "NSE")
    except InstrumentNotFoundError:
        # gracefully skip unknown symbols
        pass
    except PyZDataError as e:
        # catch-all for any other library error
        raise
"""


class PyZDataError(Exception):
    """Base exception for all PyZData errors."""


class AuthenticationError(PyZDataError):
    """Raised when login or token validation fails."""


class InstrumentNotFoundError(PyZDataError):
    """Raised when a symbol/exchange pair or token cannot be resolved."""


class DataFetchError(PyZDataError):
    """Raised when historical candle data cannot be fetched from the API."""


class ConfigurationError(PyZDataError):
    """Raised for missing or invalid configuration values."""
