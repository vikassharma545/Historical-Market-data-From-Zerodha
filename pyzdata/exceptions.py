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


class PartialDataError(DataFetchError):
    """Raised when some — but not all — date ranges of a download failed.

    The rows that *were* fetched are kept on :attr:`partial_data` so callers
    can decide whether incomplete data is still useful:

        try:
            df = client.get_data(token, start, end, Interval.MINUTE_1)
        except PartialDataError as exc:
            df = exc.partial_data          # has gaps at exc.failed_ranges
    """

    def __init__(self, message, partial_data, failed_ranges):
        super().__init__(message)
        #: Cleaned DataFrame of every range that downloaded successfully.
        self.partial_data = partial_data
        #: ``[(start_date, end_date), …]`` of the ranges that are missing.
        self.failed_ranges = failed_ranges


class ConfigurationError(PyZDataError):
    """Raised for missing or invalid configuration values."""
