# Changelog

All notable changes to PyZData are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-11

### Changed
- **Web app restyled as a trading desk:** warm grey page with white cards, one orange accent
  for actions, a dark tab for the chosen exchange / period / interval, a greeting with the
  date in IST, and a result card that leads with the last close in monospace, its change
  over the period in green or red, and a matching price line. Fonts are the ones already
  installed — nothing is fetched from a font server
- **Downloads retry until they succeed.** Network errors, timeouts, "Too many requests",
  Kite API errors and unreadable responses are retried with a short random wait
  (0.5–3 s for rate limits, 1–5 s for API errors, up to 15 s for other failures). Only a
  `TokenException` — Zerodha logged the account out — stops a download, with a
  `DataFetchError`. `PyZData.close()` (the web app's Log out) cancels a retrying download
- Date windows are fetched one at a time instead of on a thread pool; `max_workers` and
  `PYZDATA_MAX_WORKERS` are ignored (the field stays so existing code keeps working)
- `PartialDataError` is no longer raised (kept for imports); the CLI no longer exits with 2
  for partial data, and the web app's partial-data warning is gone
- The library no longer configures logging unless `log_level` / `PYZDATA_LOG_LEVEL` is
  set; the default changed from `WARNING` to unset
- The CLI prompts for a missing `--password` / `--totp` instead of requiring them as flags
- `pyzdata-web` and `streamlit run app.py` listen on localhost only and send no usage
  statistics; both now read the same settings
- Build requires `setuptools>=77`; the publish workflow runs the tests first and pins the
  PyPI action to a commit

### Fixed
- Web app: an unexpected error left the page stuck on a disabled "Downloading …" button
- Non-JSON or malformed Kite responses escaped as raw `JSONDecodeError` / `AttributeError`
  / `KeyError` instead of being retried (downloads) or raised as `AuthenticationError` (login)
- CLI `--verbose` showed no library logs, and apps with their own logging setup got every
  library message twice
- CLI printed a traceback for an unreadable date or a start date after the end date
- `search_instruments(..., exchange="nse")` returned nothing (exchange is now case-insensitive)
- Web app told credential-login users their *enctoken* was invalid when the TOTP was wrong
- `Config` now rejects `request_timeout <= 0` and `max_retries < 0` up front

## [1.1.0] - 2026-09-20

### Added
- **Rewritten web app** — one page instead of a sidebar and three tabs: login form
  (Enter submits), searchable instrument dropdown, word search for F&O contracts
  (`23000 nifty`, `banknifty fut`), one-click period and interval, price chart,
  **Excel export**, and a Kite-like theme on a two-column layout
- **Fast Excel writer** — streams the sheet XML directly (standard library only):
  460k rows in ~1 s instead of ~25 s with openpyxl
- **Enctoken validation** — `PyZData(enctoken=...)` checks the token against Kite and
  raises `AuthenticationError` immediately instead of failing mid-download
- `PyZData.user_name` and `PyZData.instruments` properties
- `PartialDataError` (subclass of `DataFetchError`) with `.partial_data` and `.failed_ranges`
- CLI reads the enctoken from `PYZDATA_ENCTOKEN` when `--enctoken` is not given
- `NCO` exchange in the web app
- Web app smoke tests using Streamlit's `AppTest`

### Changed
- **Interval-aware request windows** — ranges are split by Kite's per-request limit
  (60–2000 days depending on interval) instead of by calendar month. Five years of daily
  candles: 60 requests → 1
- **Failed date ranges are no longer dropped silently.** They are retried once; if they
  still fail, `get_data` raises `PartialDataError` (the CLI saves the partial data, warns,
  and exits with code 2). Previously the result simply had gaps
- When every request fails, the real error is raised (an expired session says so) instead
  of returning an empty DataFrame
- Symbol lookup ignores case and extra whitespace; the not-found error suggests close matches
- `web` extra now requires `streamlit>=1.55`

### Fixed
- Web app: clicking Download twice fetched everything twice, and touching any other
  control mid-download silently discarded it. Downloads now run as a background job
  that page reruns attach to; the button is disabled while one is running
- README advertised Excel export that did not exist
- Help text described Kite's per-request limits as the maximum available history

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

[1.2.0]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.6...v1.1.0
[1.0.6]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/releases/tag/v1.0.0
