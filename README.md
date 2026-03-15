# PyZData – Zerodha Historical Market Data Downloader

![GitHub repo size](https://img.shields.io/github/repo-size/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub last commit](https://img.shields.io/github/last-commit/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub issues](https://img.shields.io/github/issues/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub stars](https://img.shields.io/github/stars/vikassharma545/Historical-Market-data-From-Zerodha?style=social)

A production-grade Python library for downloading historical OHLCV and Open Interest candle data from [Zerodha](https://zerodha.com) using the Kite Connect API.

---

## Features

- Download 1-minute to daily OHLCV candles for any instrument
- Supports Open Interest (OI) for F&O instruments
- Two authentication modes: credential login (2FA/TOTP) or pre-obtained enctoken
- Parallel month-by-month downloads via a thread pool
- Instruments CSV cached on disk — no 50 MB re-download on every run
- Configurable retry strategy with exponential backoff
- Full CLI (`pyzdata` command) with CSV export
- Structured logging (no `print` statements — integrates with any logging setup)
- Typed exceptions for fine-grained error handling

---

## Architecture

```
pyzdata/
├── client.py        PyZData — public facade; wires the components together
├── auth.py          KiteAuth — two-step credential login
├── instruments.py   InstrumentManager — token lookup + disk cache
├── downloader.py    DataDownloader — parallel monthly fetches
├── models.py        Interval enum
├── config.py        Config dataclass + PYZDATA_* env-var loading
├── exceptions.py    Typed exception hierarchy
└── cli.py           `pyzdata` CLI entry point
```

Data flow:

```
PyZData.__init__
  ├─ KiteAuth.login_with_credentials()  →  enctoken
  └─ InstrumentManager.load()           →  cached CSV

PyZData.get_data()
  └─ DataDownloader.fetch()
       ├─ split range into monthly windows
       ├─ ThreadPoolExecutor (parallel HTTP)
       │    └─ GET /instruments/historical/{token}/{interval}
       └─ concat → deduplicate → sort → return DataFrame
```

---

## Installation

```bash
# From GitHub
pip install git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git

# For development (includes test dependencies)
git clone https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git
cd Historical-Market-data-From-Zerodha
pip install -e ".[dev]"
```

**Requirements:** Python >= 3.8, pandas >= 1.3, requests >= 2.25

---

## Quick Start

### Python API

```python
from pyzdata import PyZData, Interval

# --- Authentication ---

# Option A: pre-obtained enctoken (fastest — no login round-trip)
client = PyZData(enctoken="your_enctoken_here")

# Option B: credential login (handles 2FA automatically)
client = PyZData(user_id="AB1234", password="your_password", totp="123456")
# Note: totp accepts both str and int — leading zeros are safe.

# --- Discover instruments ---

# Exact lookup
token = client.get_instrument_token("NIFTY 50", "NSE")

# Partial search (useful when you don't know the exact symbol)
results = client.search_instruments("NIFTY", exchange="NSE")
print(results[["tradingsymbol", "instrument_token", "exchange"]])

# --- Download data ---

# Daily candles for a full year
df = client.get_data(token, "2024-01-01", "2024-12-31", Interval.DAY)
print(df.head())
#   tradingsymbol            datetime     open     high      low    close     volume
# 0      NIFTY 50 2024-01-02 09:15:00  21741.9  21774.2  21658.4  21737.9   142850
# ...

# 1-minute candles with Open Interest (F&O instruments)
fut_token = client.get_instrument_token("NIFTY24JANFUT", "NFO")
df_oi = client.get_data(fut_token, "2024-01-02", "2024-01-25", Interval.MINUTE_1, oi=True)
# Columns: tradingsymbol, datetime, open, high, low, close, volume, open_interest
```

### CLI

```bash
# Daily data, print to console
pyzdata --enctoken TOKEN "NIFTY 50" NSE 2024-01-01 2024-12-31

# 1-minute data, save to CSV
pyzdata --enctoken TOKEN RELIANCE NSE 2024-01-01 2024-06-30 \
        --interval minute --output reliance_1min.csv

# Credential login
pyzdata --user-id AB1234 --password pw --totp 123456 \
        RELIANCE NSE 2024-01-01 2024-01-31

# Search for instruments
pyzdata --enctoken TOKEN search NIFTY --exchange NSE

# Show all options
pyzdata --help
```

---

## Configuration

All settings can be overridden via environment variables.  Copy `.env.example`
to `.env` and fill in your values (use [python-dotenv](https://pypi.org/project/python-dotenv/)
to load them automatically).

| Variable | Default | Description |
|----------|---------|-------------|
| `PYZDATA_MAX_WORKERS` | `4` | Parallel download threads |
| `PYZDATA_MAX_RETRIES` | `5` | Retry attempts on transient failures |
| `PYZDATA_BACKOFF_FACTOR` | `1.0` | Exponential backoff base (seconds) |
| `PYZDATA_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `PYZDATA_CACHE_TTL_HOURS` | `24` | Instruments cache lifetime |
| `PYZDATA_CACHE_PATH` | `~/.pyzdata/instruments.csv` | Cache file location |
| `PYZDATA_LOG_LEVEL` | `WARNING` | Log level: DEBUG, INFO, WARNING, ERROR |

Or pass a `Config` object directly:

```python
from pyzdata import Config, PyZData

cfg = Config(max_workers=8, log_level="DEBUG", instruments_cache_ttl_hours=12)
client = PyZData(enctoken="...", config=cfg)
```

---

## Logging

PyZData uses Python's standard `logging` module under the `pyzdata` namespace.
No `print` statements — output is fully controlled by the host application:

```python
import logging

# Show all internal messages
logging.basicConfig(level=logging.DEBUG)

# Or configure just the pyzdata logger
logging.getLogger("pyzdata").setLevel(logging.INFO)
```

---

## Error Handling

```python
from pyzdata import PyZData, Interval
from pyzdata.exceptions import (
    AuthenticationError,
    InstrumentNotFoundError,
    DataFetchError,
    PyZDataError,   # catch-all base class
)

try:
    client = PyZData(enctoken="...")
    token  = client.get_instrument_token("INVALID_SYM", "NSE")
except AuthenticationError as e:
    print(f"Login failed: {e}")
except InstrumentNotFoundError as e:
    print(f"Symbol not found: {e}")
except DataFetchError as e:
    print(f"Data fetch failed: {e}")
except PyZDataError as e:
    print(f"PyZData error: {e}")
```

---

## Available Intervals

| Enum | API value | Description |
|------|-----------|-------------|
| `Interval.MINUTE_1` | `minute` | 1-minute candles |
| `Interval.MINUTE_3` | `3minute` | 3-minute candles |
| `Interval.MINUTE_5` | `5minute` | 5-minute candles |
| `Interval.MINUTE_10` | `10minute` | 10-minute candles |
| `Interval.MINUTE_15` | `15minute` | 15-minute candles |
| `Interval.MINUTE_30` | `30minute` | 30-minute candles |
| `Interval.HOUR_1` | `60minute` | 1-hour candles |
| `Interval.DAY` | `day` | Daily candles |

---

## GUI for Non-Programmers

A standalone Windows `.exe` with a graphical interface is available in the repo.
No Python installation required.

### Login Screen
![Login GUI](/assets/login.png)

### Download Screen
![Download GUI](/assets/download.png)

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

Tests use mocked HTTP sessions — no real Zerodha credentials or network access
are required.

---

## Migrating from v0.1

| v0.1 | v1.0 |
|------|------|
| `get_data(..., print_logs=True)` | Use `logging.basicConfig(level=logging.INFO)` |
| `from pyzdata.pyzdata import PyZData` | `from pyzdata import PyZData` |
| `totp=123456` (int) | `totp="123456"` or `totp=123456` — both work |
| No CLI | `pyzdata --help` |
| No typed exceptions | `except DataFetchError` etc. |

---

## License

MIT License — see [LICENSE](LICENSE).

## Author

Developed by [Vikas Sharma](https://github.com/vikassharma545)
