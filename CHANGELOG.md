# Changelog

All notable changes to PyZData are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.6] - 2025-03-28

### Added
- **Context manager support** — `with PyZData(...) as client:` automatically closes the HTTP session
- **Proactive API rate limiting** — configurable `rate_limit_per_second` (default 3 req/s) via `PYZDATA_RATE_LIMIT`
- Environment variable validation with clear `ConfigurationError` messages
- 17 new tests (app helpers, throttle) — test count: 73 → 90

### Fixed
- **Thread-safe progress counter** in parallel downloads (race condition on `completed` variable)
- Bare `except Exception` in auth 2FA response parsing — now catches only `ValueError`/`JSONDecodeError`
- Bare `except Exception` in version detection — now catches only `PackageNotFoundError`/`ModuleNotFoundError`
- Non-atomic instruments cache writes — now uses `.tmp` + `replace()` to prevent corruption

### Changed
- Added Python 3.13 to CI test matrix and classifiers
- Added ruff linting step to CI pipeline
- Removed duplicate `requirements-dev.txt` (single source of truth in `pyproject.toml`)

## [1.0.5] - 2025-03-28

### Changed
- Enhanced download progress feedback with per-month counters in CLI and web UI

## [1.0.4] - 2025-03-27

### Changed
- **Minimum Python version raised to 3.10+** (`requires-python = ">=3.10"`)

## [1.0.3] - 2025-03-26

### Fixed
- Lowered Streamlit render limit to 2 000 rows to prevent browser hanging on large datasets

### Changed
- Force light theme and remove deploy button in Streamlit UI

## [1.0.2] - 2025-03-25

### Fixed
- Fixed dark mode by replacing hardcoded light backgrounds with rgba colours
- Fixed `StreamlitAPIException` caused by mutating widget keys after instantiation
- Fixed Streamlit rerun bugs, key-based widget state, and auth 2FA status check

### Added
- `pyzdata-web` console script for installed users (`pip install "pyzdata[web]"`)

## [1.0.1] - 2025-03-20

### Added
- GitHub Actions CI for testing on Python 3.10 / 3.11 / 3.12
- GitHub Actions workflow for automated PyPI publishing via Trusted Publishing (OIDC)
- PyPI version badge in README

### Changed
- Updated PyPI description; clarified no API subscription is required

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

[1.0.6]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/releases/tag/v1.0.0
