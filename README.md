# PyZData – Zerodha Historical Market Data Downloader

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub repo size](https://img.shields.io/github/repo-size/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub last commit](https://img.shields.io/github/last-commit/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub stars](https://img.shields.io/github/stars/vikassharma545/Historical-Market-data-From-Zerodha?style=social)

Download historical OHLCV and Open Interest candle data for any stock, index, or F&O instrument from **Zerodha** — as a Python library, a CLI command, or a browser-based web app.

---

## What you can do with PyZData

- Download price history for **any stock or index** listed on Zerodha (NSE, BSE, NFO, MCX)
- Choose intervals from **1-minute to daily**
- Export clean **pandas DataFrames** ready for backtesting, charting, or ML
- Use the **web app** — no coding needed
- Use the **CLI** — one-liner downloads from the terminal
- Use the **Python library** — import and integrate into your own scripts

---

## Web Interface (no coding required)

The easiest way to use PyZData is the built-in Streamlit web app.

**Run it:**

```bash
pip install "git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git#egg=pyzdata[web]"
pyzdata-web
```

Then open `http://localhost:8501` in your browser.

**Features:**
- Click popular stocks (NIFTY 50, RELIANCE, TCS, HDFC Bank …) — no typing needed
- Quick date presets: Last Week, Last Month, Last Year, Last 3 Years …
- Plain-English frequency selector with descriptions
- Download result as **CSV** or **Excel (.xlsx)**
- Built-in Help tab with step-by-step guides

---

## Installation

```bash
# Library only (Python API + CLI)
pip install git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git

# Library + web interface (adds streamlit and openpyxl)
pip install "git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git#egg=pyzdata[web]"
```

**Requirements:** Python 3.8+, pandas ≥ 1.3, requests ≥ 2.25

For development:

```bash
git clone https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git
cd Historical-Market-data-From-Zerodha
pip install -e ".[web,dev]"
```

---

## Python Library

```python
from pyzdata import PyZData, Interval

# Login with enctoken (paste from browser cookies after logging into kite.zerodha.com)
client = PyZData(enctoken="your_enctoken_here")

# OR login with credentials
client = PyZData(user_id="AB1234", password="your_password", totp="123456")

# Find the instrument token for a symbol
token = client.get_instrument_token("NIFTY 50", "NSE")

# Not sure of the exact symbol name? Search for it
results = client.search_instruments("NIFTY", exchange="NSE")
print(results[["tradingsymbol", "instrument_token", "exchange"]])

# Download daily candles for a full year
df = client.get_data(token, "2024-01-01", "2024-12-31", Interval.DAY)
print(df.head())

# Download 1-minute candles with Open Interest (F&O instruments)
fut_token = client.get_instrument_token("NIFTY24JANFUT", "NFO")
df = client.get_data(fut_token, "2024-01-02", "2024-01-25", Interval.MINUTE_1, oi=True)
```

**Output columns:** `tradingsymbol, datetime, open, high, low, close, volume` (+ `open_interest` when `oi=True`)

---

## CLI

```bash
# Daily data for NIFTY 50 — print to terminal
pyzdata download --enctoken TOKEN --symbol "NIFTY 50" --exchange NSE \
        --start 2024-01-01 --end 2024-12-31

# 1-minute data — save to CSV
pyzdata download --enctoken TOKEN --symbol RELIANCE --exchange NSE \
        --start 2024-01-01 --end 2024-06-30 \
        --interval minute --output reliance.csv

# Login with credentials
pyzdata download --user-id AB1234 --password pw --totp 123456 \
        --symbol RELIANCE --exchange NSE \
        --start 2024-01-01 --end 2024-01-31

# Search for a symbol
pyzdata search --enctoken TOKEN --query HDFC --exchange NSE

# All options
pyzdata download --help
pyzdata search --help
```

---

## Available Intervals

| Enum | Interval | Best for |
|------|----------|----------|
| `Interval.MINUTE_1` | 1 minute | Intraday scalping analysis |
| `Interval.MINUTE_5` | 5 minutes | Intraday charts |
| `Interval.MINUTE_15` | 15 minutes | Intraday / short-term |
| `Interval.MINUTE_30` | 30 minutes | Swing trading |
| `Interval.HOUR_1` | 1 hour | Swing / positional |
| `Interval.DAY` | Daily | Long-term investing & backtesting |

---

## Configuration

Copy `.env.example` to `.env` and set any values you want to override:

| Variable | Default | Description |
|----------|---------|-------------|
| `PYZDATA_MAX_WORKERS` | `4` | Parallel download threads |
| `PYZDATA_MAX_RETRIES` | `5` | Retry attempts on failures |
| `PYZDATA_TIMEOUT` | `30` | HTTP timeout in seconds |
| `PYZDATA_CACHE_TTL_HOURS` | `24` | How long to cache the instruments list |
| `PYZDATA_LOG_LEVEL` | `WARNING` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

Or pass a `Config` object in code:

```python
from pyzdata import Config, PyZData

cfg = Config(max_workers=8, log_level="DEBUG")
client = PyZData(enctoken="...", config=cfg)
```

---

## Error Handling

```python
from pyzdata.exceptions import (
    AuthenticationError,    # wrong credentials or expired enctoken
    InstrumentNotFoundError, # symbol not found
    DataFetchError,          # API or network failure
    PyZDataError,            # catch-all base class
)

try:
    client = PyZData(enctoken="...")
    token  = client.get_instrument_token("RELIANCE", "NSE")
    df     = client.get_data(token, "2024-01-01", "2024-12-31", Interval.DAY)
except AuthenticationError as e:
    print(f"Login failed: {e}")
except InstrumentNotFoundError as e:
    print(f"Symbol not found: {e}")
except DataFetchError as e:
    print(f"Download failed: {e}")
```

---

## Project Structure

```
pyzdata/
├── client.py        PyZData — main entry point
├── auth.py          Two-step Zerodha login
├── instruments.py   Symbol lookup with 24-hour disk cache
├── downloader.py    Parallel monthly data fetching
├── models.py        Interval enum
├── config.py        Settings + environment variable loading
├── exceptions.py    Typed exception hierarchy
├── cli.py           pyzdata command-line tool
├── _app.py          Streamlit web interface
└── py.typed         PEP 561 type-checking marker

app.py               Local dev launcher for Streamlit
tests/               Unit tests (no credentials needed)
CONTRIBUTING.md      How to contribute
CHANGELOG.md         Release history
SECURITY.md          Security policy
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

No Zerodha account or internet connection needed — all HTTP calls are mocked.

---

## How to get your enctoken

1. Log in to [kite.zerodha.com](https://kite.zerodha.com)
2. Press **F12** → **Application** tab → **Cookies** → `kite.zerodha.com`
3. Copy the value of the `enctoken` cookie
4. Paste it into the app or pass it as `PyZData(enctoken="...")`

The enctoken refreshes each time you log in to Kite.

---

## License

MIT — see [LICENSE](LICENSE)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Author

Built by [Vikas Sharma](https://github.com/vikassharma545)
