# PyZData 1.1.0 — simpler web app + UX fixes in the library

Date: 2026-09-20
Status: approved

## Goal

Make PyZData simpler and smoother to use. Rewrite the Streamlit web app as a
single-page flow and fix the library behaviours that surface as bad UX. The
public Python API and CLI stay backward compatible.

## Audit findings being addressed

1. An enctoken is never validated at login; a bad token only fails later, at
   download time, as a raw `HTTP 403`.
2. In multi-window downloads, failed windows are logged and replaced with an
   empty frame — the user gets data with silent gaps, or "No data returned"
   when every window failed (e.g. expired session).
3. All intervals are fetched in calendar-month windows. Daily candles allow
   ~2000 days per request, so 5 years of daily data costs 60 throttled
   requests instead of 1.
4. Symbol lookup is exact and case-sensitive; the web app sends users to a
   separate Search tab to copy-paste symbols.
5. README promises Excel export (not implemented). The Help tab presents
   Kite's per-request limits as "maximum history", which is wrong.
6. Web app: sidebar login, three tabs, 24 rerun-forcing buttons, staging-key
   hacks, duplicate exchange selector, CSS bound to Streamlit internals,
   balloons + forced rerun, no chart, broken markdown on the welcome screen.

## Library changes

### Enctoken validation (`auth.py`, `client.py`, `config.py`)

- `Config.profile_url = "https://kite.zerodha.com/oms/user/profile"`.
- `KiteAuth.fetch_profile(enctoken) -> dict`: GET `profile_url` with the auth
  header. HTTP 401/403 or `status != "success"` → `AuthenticationError(
  "Invalid or expired enctoken. …")`. Network failure → `AuthenticationError`
  mentioning the network.
- `PyZData.__init__` calls it on the enctoken path only (a credential login
  has just produced a fresh token). Result is stored; `client.user_name`
  returns the profile's `user_name` (falls back to `user_id`, then `None` on
  the credential path).

### Interval-aware windows (`downloader.py`)

- `_month_windows` is replaced by `_date_windows(from_dt, to_dt, max_days)`.
- `max_days` per interval (Kite per-request limits): under 5 minutes → 60;
  5 and 10 minute → 100; 15 and 30 minute → 200; 60 minute and 2/3/4 hour →
  400; day → 2000.
- The progress callback keeps its `(completed, total)` signature; the unit is
  now "parts", not months.

### No silent gaps (`downloader.py`, `exceptions.py`)

- Windows that fail in the parallel pass are retried once, sequentially.
- All windows failed → raise the first `DataFetchError` (HTTP 401/403 gets a
  message saying the session has expired).
- Some windows failed → raise `PartialDataError(DataFetchError)` with
  `.partial_data` (cleaned DataFrame of what succeeded) and `.failed_ranges`
  (list of `(date, date)`).
- This is the one intentional behaviour change: scripts that previously got
  silently incomplete data now get an exception that carries the data.

### Forgiving symbol lookup (`instruments.py`)

- `get_token`: exact match first; fall back to a match that ignores case and
  surrounding/repeated whitespace. The not-found error lists up to 5 close
  matches from `search`.

### CLI (`cli.py`)

- `--enctoken` falls back to the `PYZDATA_ENCTOKEN` environment variable so
  tokens need not appear in shell history. Explicit flags win.

## Web app

One page, no sidebar, no tabs. UI in `pyzdata/_app.py`; Streamlit-free helpers
in `pyzdata/_web_helpers.py`.

- **Login**: centered form (Enter submits). Enctoken by default; a segmented
  control switches to User ID / password / TOTP. Enctoken how-to and safety
  notes in expanders. Errors mapped to friendly text.
- **Header**: title, "Logged in as …", Log out (closes the client session).
- **1 · Instrument**: exchange segmented control (NSE default). NSE/BSE/CDS →
  one searchable selectbox labelled `SYMBOL — name`, popular picks first.
  NFO/BFO/MCX → underlying selectbox, then contract selectbox.
- **2 · Period**: pills `1W 1M 3M 6M 1Y 3Y 5Y Custom`; date inputs only for
  Custom.
- **3 · Interval**: pills `Day 1h 30m 15m 5m 1m`, remaining intervals in a
  "More intervals" selectbox.
- **Open interest** checkbox shown only for F&O exchanges.
- **Download**: progress bar → result stored in session state as CSV bytes +
  small chart/preview frames (never the full DataFrame). Result panel: row
  count, date range, last close; close-price line chart (downsampled to ≤ 2000
  points); first rows preview; CSV and Excel download buttons. Excel is built
  lazily and disabled above 1,048,575 rows. `PartialDataError` → warning that
  names the missing ranges, partial data still offered.
- **Help**: one expander, corrected content.
- Removed: balloons, forced reruns, `_sym_next` staging keys, `data-testid`
  CSS, the Search tab, the duplicate exchange override.

## Packaging and docs

- `web` extra adds `openpyxl`. Version → 1.1.0.
- README, CHANGELOG, Help text updated; wrong "maximum history" table removed.

## Testing

- Library changes are test-first; existing window/lookup tests are updated.
- `_web_helpers` gets plain unit tests.
- `streamlit.testing.v1.AppTest` smoke tests: login screen renders; logged-in
  page renders with a fake client.

## Risk

Zerodha cannot be reached without credentials from the dev environment. The
profile check and the larger request windows follow Kite's documented limits
and are verified against mocks only; one real login + download is needed to
confirm them.
