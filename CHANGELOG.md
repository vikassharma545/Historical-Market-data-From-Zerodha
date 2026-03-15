# Changelog

All notable changes to PyZData are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-03-15

### Added
- **Python library** — `PyZData` client with `get_data()`, `get_instrument_token()`, `search_instruments()`
- **CLI** — `pyzdata` command with download and search sub-commands
- **Web interface** — Streamlit app with popular stock shortcuts, date presets, and CSV/Excel export
- **Authentication** — two-step credential login (user ID + password + TOTP) and enctoken-based auth
- **Parallel downloads** — multi-threaded month-window fetching for faster data retrieval
- **Instruments caching** — 24-hour disk cache for the instruments master CSV
- **Configuration** — `Config` dataclass with `PYZDATA_*` environment variable support
- **Exception hierarchy** — `PyZDataError` base with typed subclasses (`AuthenticationError`, `InstrumentNotFoundError`, `DataFetchError`, `ConfigurationError`)
- **Retry with backoff** — configurable exponential backoff on transient HTTP failures
- **Interval enum** — `Interval` enum covering 1-minute to daily candle granularity
- **Unit tests** — comprehensive mocked tests for auth, instruments, and downloader
- **Open Interest** — optional `open_interest` column for F&O instruments

[1.0.0]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/releases/tag/v1.0.0
