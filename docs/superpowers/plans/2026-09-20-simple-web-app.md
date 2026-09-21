# PyZData 1.1.0 Implementation Plan

**Goal:** Single-page Streamlit app plus the library fixes that make it smooth.

**Architecture:** Library fixes land first (each test-first, each its own
commit) so the app can rely on them. The app is split into Streamlit-free
helpers (`_web_helpers.py`, unit-tested) and UI (`_app.py`, smoke-tested with
`streamlit.testing.v1.AppTest`).

**Tech stack:** Python 3.10+, pandas, requests, Streamlit ≥ 1.50, openpyxl, pytest.

**Spec:** `docs/superpowers/specs/2026-09-20-simple-web-app-design.md`

## Global constraints

- Public API stays backward compatible (`PyZData`, `Interval`, `Config`, CLI flags).
- Only intentional behaviour change: partial downloads raise `PartialDataError`.
- `pytest` and `ruff check .` must pass after every task.
- No real network calls in tests.

---

### Task 1: Forgiving symbol lookup
- Modify `pyzdata/instruments.py` (`get_token`), test `tests/test_instruments.py`.
- Produces: `get_token("reliance ", "nse")` resolves; not-found message lists close matches.

### Task 2: Interval-aware windows
- Modify `pyzdata/downloader.py`, test `tests/test_downloader.py`.
- Produces: `_date_windows(from_dt, to_dt, max_days)`, `_max_days(interval) -> int`
  (60 / 100 / 200 / 400 / 2000). `_month_windows` removed.

### Task 3: No silent gaps
- Modify `pyzdata/exceptions.py`, `pyzdata/downloader.py`, `pyzdata/__init__.py`; test `tests/test_downloader.py`.
- Produces: `PartialDataError(message, partial_data: DataFrame, failed_ranges: list[tuple[date, date]])`;
  one sequential retry of failed windows; all failed → first `DataFetchError`;
  HTTP 401/403 message says the session expired.

### Task 4: Enctoken validation
- Modify `pyzdata/config.py`, `pyzdata/auth.py`, `pyzdata/client.py`; tests `tests/test_auth.py`, new `tests/test_client.py`.
- Produces: `Config.profile_url`, `KiteAuth.fetch_profile(enctoken) -> dict`, `PyZData.user_name -> str | None`.

### Task 5: CLI env fallback
- Modify `pyzdata/cli.py`, test `tests/test_cli.py`.
- Produces: `PYZDATA_ENCTOKEN` used when neither `--enctoken` nor `--user-id` is given.

### Task 6: Web helpers
- Create `pyzdata/_web_helpers.py`, `tests/test_web_helpers.py`; delete `tests/test_app_helpers.py`.
- Produces: `EXCHANGES`, `FNO_EXCHANGES`, `PERIODS`, `MAIN_INTERVALS`, `MORE_INTERVALS`,
  `POPULAR`, `period_to_dates`, `instrument_options`, `underlyings`, `contract_options`,
  `friendly_error`, `to_excel_bytes`, `chart_frame`, `file_stem`, `EXCEL_MAX_ROWS`.

### Task 7: Web app rewrite
- Rewrite `pyzdata/_app.py`; create `tests/test_app_smoke.py`; add `PyZData.instruments` (read-only DataFrame).
- Smoke tests: login screen renders without exception; logged-in page renders with a fake client.

### Task 8: Packaging and docs
- `pyproject.toml` (version 1.1.0, `openpyxl` in `web`), `pyzdata/__init__.py` version,
  `README.md`, `CHANGELOG.md`, `.streamlit/config.toml` if needed.
- Final: full `pytest`, `ruff check .`, launch the app and look at the login screen.
