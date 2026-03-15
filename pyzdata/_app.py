"""PyZData Web Interface — designed for every user, not just developers.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from pyzdata import Config, Interval, PyZData, __version__
from pyzdata.exceptions import (
    AuthenticationError,
    DataFetchError,
    InstrumentNotFoundError,
    PyZDataError,
)

# ─────────────────────────────────────────────────────────────────────────────
# Data tables  (no external API calls needed)
# ─────────────────────────────────────────────────────────────────────────────

# (symbol, exchange, friendly label, emoji)
POPULAR_STOCKS: List[Tuple[str, str, str, str]] = [
    ("NIFTY 50",    "NSE", "NIFTY 50",       "📈"),
    ("NIFTY BANK",  "NSE", "BANK NIFTY",     "🏦"),
    ("RELIANCE",    "NSE", "Reliance",        "⚡"),
    ("TCS",         "NSE", "TCS",             "💻"),
    ("HDFCBANK",    "NSE", "HDFC Bank",       "🏛️"),
    ("INFY",        "NSE", "Infosys",         "🖥️"),
    ("ICICIBANK",   "NSE", "ICICI Bank",      "🏧"),
    ("SBIN",        "NSE", "SBI",             "🏦"),
    ("ITC",         "NSE", "ITC",             "🌿"),
    ("WIPRO",       "NSE", "Wipro",           "💡"),
    ("BAJFINANCE",  "NSE", "Bajaj Finance",   "💳"),
    ("TATAMOTORS",  "NSE", "Tata Motors",     "🚗"),
    ("HINDUNILVR",  "NSE", "HUL",             "🧴"),
    ("AXISBANK",    "NSE", "Axis Bank",       "💰"),
    ("MARUTI",      "NSE", "Maruti Suzuki",   "🚙"),
    ("ONGC",        "NSE", "ONGC",            "🛢️"),
    ("SENSEX",      "BSE", "SENSEX",          "📊"),
]

# Human-readable label → (Interval, description)
FREQUENCY_OPTIONS: Dict[str, Tuple[Interval, str]] = {
    "📅  Daily  (recommended for beginners)": (
        Interval.DAY,
        "One data point per trading day. Best for understanding long-term price trends.",
    ),
    "⏰  Hourly": (
        Interval.HOUR_1,
        "One data point per hour. Good for weekly or monthly analysis.",
    ),
    "🕐  Every 30 Minutes": (
        Interval.MINUTE_30,
        "Half-hourly candles. Suitable for short-term swing trading.",
    ),
    "⚡  Every 15 Minutes": (
        Interval.MINUTE_15,
        "Commonly used for intraday trading charts.",
    ),
    "🔬  Every 5 Minutes": (
        Interval.MINUTE_5,
        "High-detail intraday data. File size gets large over long periods.",
    ),
    "🧬  Every Minute": (
        Interval.MINUTE_1,
        "Most detailed data available. Only use for short date ranges.",
    ),
}

# Label → days offset from today
DATE_PRESETS: dict[str, int] = {
    "Last 1 Week":   7,
    "Last 1 Month":  30,
    "Last 3 Months": 90,
    "Last 6 Months": 180,
    "Last 1 Year":   365,
    "Last 3 Years":  1095,
    "Last 5 Years":  1825,
}

EXCHANGES = ["NSE", "BSE", "NFO", "MCX", "CDS", "BFO"]

# ─────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ss(key: str, default=None):
    """Read from session_state with a default."""
    return st.session_state.get(key, default)


def is_logged_in() -> bool:
    return st.session_state.get("client") is not None


def get_client() -> PyZData | None:
    return st.session_state.get("client")


def _set_stock(symbol: str, exchange: str) -> None:
    # Write to staging keys — the real "sym"/"exch" keys are owned by already-
    # rendered widgets in this run and cannot be mutated after instantiation.
    # On the next rerun, render_download_tab() moves these into "sym"/"exch"
    # BEFORE the widgets are created, so Streamlit accepts the update.
    st.session_state["_sym_next"]  = symbol
    st.session_state["_exch_next"] = exchange


def _set_dates(days: int) -> None:
    st.session_state["end_date"]   = date.today()
    st.session_state["start_date"] = date.today() - timedelta(days=days)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    st.sidebar.markdown("# 📊 PyZData")
    st.sidebar.caption(f"v{__version__} • Free • Open source • No signup needed")
    st.sidebar.divider()

    if is_logged_in():
        st.sidebar.success("You are logged in ✅")
        if st.sidebar.button("🚪  Log out", use_container_width=True):
            for k in ["client", "last_df", "last_meta", "sym", "exch"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.sidebar.divider()
        st.sidebar.info(
            "Your session is active. Data will download as long as this "
            "browser tab is open."
        )
        return

    # ── Not logged in ──
    st.sidebar.subheader("🔑  Step 1: Log in to Zerodha")

    auth_tab = st.sidebar.radio(
        "Choose login method",
        ["Paste Enctoken", "Enter username & password"],
        index=0,
        help="Both methods are equally secure.",
    )

    if auth_tab == "Paste Enctoken":
        _sidebar_enctoken_form()
    else:
        _sidebar_credential_form()

    st.sidebar.divider()

    with st.sidebar.expander("❓  How do I get my enctoken?"):
        st.markdown("""
**Step-by-step (takes 2 minutes):**

1. Open [kite.zerodha.com](https://kite.zerodha.com) and **log in** with your Zerodha ID.
2. Press **F12** on your keyboard to open Developer Tools.
3. Click the **"Application"** tab at the top (Chrome) or **"Storage"** tab (Firefox).
4. On the left panel, expand **Cookies** → click **kite.zerodha.com**.
5. In the table, find the row named **`enctoken`**.
6. Click on it and **copy the long value** in the bottom panel.
7. Paste it in the box above and click Login.

> **Note:** Your enctoken changes each time you log in to Kite. If login stops working, repeat these steps.
""")

    with st.sidebar.expander("🔒  Is this safe?"):
        st.markdown("""
- Your credentials are sent **directly to Zerodha's servers** — not stored anywhere else.
- This app runs **entirely in your browser** and on your own computer.
- The source code is **open source** — anyone can inspect it.
- We never save your password or enctoken to a file.
""")


def _sidebar_enctoken_form() -> None:
    enctoken = st.sidebar.text_input(
        "Your enctoken",
        type="password",
        placeholder="Paste the long token here …",
    )
    if st.sidebar.button("Login →", type="primary", use_container_width=True):
        if not enctoken.strip():
            st.sidebar.error("Please paste your enctoken first.")
            return
        _do_login(enctoken=enctoken.strip())


def _sidebar_credential_form() -> None:
    user_id  = st.sidebar.text_input("Zerodha User ID", placeholder="e.g. AB1234")
    password = st.sidebar.text_input("Password", type="password")
    totp     = st.sidebar.text_input(
        "TOTP (6-digit code)",
        placeholder="From your authenticator app",
        max_chars=6,
        help="Open your Google Authenticator / Zerodha Authenticator app for this code.",
    )
    if st.sidebar.button("Login →", type="primary", use_container_width=True):
        missing = [n for n, v in [("User ID", user_id), ("Password", password), ("TOTP", totp)] if not v.strip()]
        if missing:
            st.sidebar.error(f"Please fill in: {', '.join(missing)}")
            return
        _do_login(user_id=user_id.strip(), password=password.strip(), totp=totp.strip())


def _do_login(**kwargs) -> None:
    with st.sidebar:
        with st.spinner("Connecting to Zerodha …"):
            try:
                client = PyZData(config=Config(log_level="ERROR"), **kwargs)
                st.session_state["client"] = client
                st.rerun()
            except AuthenticationError as exc:
                st.error(f"Login failed — {_friendly_auth_error(str(exc))}")
            except PyZDataError as exc:
                st.error(f"Something went wrong: {exc}")


def _friendly_auth_error(msg: str) -> str:
    msg_lower = msg.lower()
    if "403" in msg_lower or "password" in msg_lower:
        return "Wrong User ID or password. Please check and try again."
    if "totp" in msg_lower or "2fa" in msg_lower or "twofa" in msg_lower:
        return "Wrong TOTP code. Open your authenticator app and use the latest 6-digit code."
    if "enctoken" in msg_lower:
        return "Invalid or expired enctoken. Please get a fresh one from Kite (see the guide below)."
    if "network" in msg_lower or "connect" in msg_lower:
        return "Network error. Check your internet connection and try again."
    return msg


# ─────────────────────────────────────────────────────────────────────────────
# Welcome screen  (shown before login)
# ─────────────────────────────────────────────────────────────────────────────

def render_welcome() -> None:
    st.markdown("""
## 👋  Welcome to PyZData
### The easiest way to download Indian stock market data
""")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="info-card">
<b>📥  Download any stock</b><br><br>
Get historical price data for stocks, indices, F&amp;O, and commodities traded on Zerodha.
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="info-card">
<b>📊  Any time period</b><br><br>
Choose from last week all the way to 5 years of data, or pick custom dates.
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="info-card">
<b>💾  Save as Excel or CSV</b><br><br>
Download your data instantly as a spreadsheet. Ready for Excel, Google Sheets, or Python.
</div>
""", unsafe_allow_html=True)

    st.divider()

    st.markdown("### How to get started")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("**Step 1 — Log in** (sidebar ←)**\n\nPaste your Zerodha enctoken OR enter your username, password, and TOTP.")
    with s2:
        st.markdown("**Step 2 — Pick a stock**\n\nChoose from popular stocks or type any symbol traded on Zerodha.")
    with s3:
        st.markdown("**Step 3 — Download**\n\nSelect a date range and click Download. Save to your computer with one click.")

    st.divider()
    st.info("👈  **Get started by logging in using the left sidebar.**")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Download Data
# ─────────────────────────────────────────────────────────────────────────────

def render_download_tab() -> None:
    if not is_logged_in():
        render_welcome()
        return

    # Apply any pending stock selection from chip buttons.  Must happen BEFORE
    # the text_input / selectbox widgets are instantiated, otherwise Streamlit
    # raises "cannot be modified after the widget … is instantiated".
    if "_sym_next" in st.session_state:
        st.session_state["sym"]  = st.session_state.pop("_sym_next")
    if "_exch_next" in st.session_state:
        st.session_state["exch"] = st.session_state.pop("_exch_next")

    client = get_client()

    # ── Step 1: Pick a stock ──────────────────────────────────────────────
    st.markdown('<p class="step-header">Step 1 &nbsp;—&nbsp; Which stock do you want data for?</p>', unsafe_allow_html=True)

    sym_col, exch_col = st.columns([3, 1])
    with sym_col:
        symbol = st.text_input(
            "Type a stock or index name",
            key="sym",
            placeholder="e.g.  NIFTY 50,  RELIANCE,  HDFCBANK,  TCS …",
            label_visibility="collapsed",
            help="Enter the exact trading symbol. If unsure, use the 🔍 Search tab.",
        )

    with exch_col:
        exchange = st.selectbox(
            "Exchange",
            EXCHANGES,
            key="exch",
            label_visibility="collapsed",
            help="NSE = National Stock Exchange (most stocks). NFO = Futures & Options.",
        )

    # Popular stock shortcuts
    st.caption("Or click a popular one:")
    COLS_PER_ROW = 8
    rows = [POPULAR_STOCKS[i:i+COLS_PER_ROW] for i in range(0, len(POPULAR_STOCKS), COLS_PER_ROW)]
    for row in rows:
        cols = st.columns(len(row))
        for col, (sym, exch, label, emoji) in zip(cols, row):
            if col.button(f"{emoji}  {label}", key=f"chip_{sym}", use_container_width=True):
                _set_stock(sym, exch)
                st.rerun()

    st.divider()

    # ── Step 2: Pick a date range ─────────────────────────────────────────
    st.markdown('<p class="step-header">Step 2 &nbsp;—&nbsp; How far back do you want data?</p>', unsafe_allow_html=True)

    # Preset quick buttons
    preset_cols = st.columns(len(DATE_PRESETS))
    for col, (label, days) in zip(preset_cols, DATE_PRESETS.items()):
        if col.button(label, key=f"preset_{days}", use_container_width=True):
            _set_dates(days)
            st.rerun()

    # Actual date pickers (auto-filled by presets or manually chosen)
    d1, d2 = st.columns(2)
    with d1:
        start_date = st.date_input(
            "From date",
            key="start_date",
            max_value=date.today(),
        )
    with d2:
        end_date = st.date_input(
            "To date",
            key="end_date",
            max_value=date.today(),
        )

    if start_date > end_date:
        st.error("The start date can't be after the end date. Please fix the dates.")
        return

    st.divider()

    # ── Step 3: Pick data frequency ───────────────────────────────────────
    st.markdown('<p class="step-header">Step 3 &nbsp;—&nbsp; How often should the data be recorded?</p>', unsafe_allow_html=True)

    freq_label = st.radio(
        "Data frequency",
        list(FREQUENCY_OPTIONS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    interval, freq_desc = FREQUENCY_OPTIONS[freq_label]
    st.caption(f"ℹ️  {freq_desc}")

    # ── Advanced options (collapsed) ─────────────────────────────────────
    with st.expander("⚙️  Advanced options"):
        oi = st.checkbox(
            "Include Open Interest (OI)",
            value=False,
            help="Only useful for F&O instruments (NFO / MCX). Adds an extra column.",
        )
        custom_exchange = st.selectbox(
            "Override exchange",
            ["Use selection above"] + EXCHANGES,
            help="Change this only if your instrument is on a different exchange.",
        )
        if custom_exchange != "Use selection above":
            exchange = custom_exchange

    st.divider()

    # ── Download button ───────────────────────────────────────────────────
    current_sym = symbol.strip()

    if not current_sym:
        st.info("👆  Pick a stock above, then click Download.")
        return

    # Summary of what will be downloaded
    months = max(1, (end_date.year - start_date.year)*12 + (end_date.month - start_date.month) + 1)
    st.markdown(
        f"**Ready to download:** &nbsp; `{current_sym}` on `{exchange}` "
        f"&nbsp;|&nbsp; {start_date} → {end_date} "
        f"&nbsp;|&nbsp; {freq_label.split('  ')[1].split('(')[0].strip()} "
        f"&nbsp;|&nbsp; ~{months} month(s)"
    )

    if st.button("🚀  Download Data", type="primary", use_container_width=True):
        _execute_download(client, current_sym, exchange, start_date, end_date, interval, oi, freq_label)

    # ── Show last result ──────────────────────────────────────────────────
    if _ss("last_df") is not None:
        _render_results(_ss("last_df"), _ss("last_meta", {}))


def _execute_download(
    client:     PyZData,
    symbol:     str,
    exchange:   str,
    start_date: date,
    end_date:   date,
    interval:   Interval,
    oi:         bool,
    freq_label: str = "",
) -> None:
    # Resolve token
    with st.spinner(f"Looking up {symbol} on {exchange} …"):
        try:
            token = client.get_instrument_token(symbol, exchange)
        except InstrumentNotFoundError:
            st.error(
                f"**{symbol}** was not found on **{exchange}**. "
                "Common fixes:\n"
                "- Check the spelling (symbols are case-sensitive)\n"
                "- Use the **🔍 Search** tab to find the exact symbol name\n"
                "- Try a different exchange (e.g. NSE vs BSE)"
            )
            return
        except PyZDataError as exc:
            st.error(f"Error: {exc}")
            return

    # Fetch data
    with st.spinner(
        f"Downloading data for **{symbol}** … this may take a few seconds for long date ranges."
    ):
        try:
            df = client.get_data(token, str(start_date), str(end_date), interval, oi=oi)
        except DataFetchError as exc:
            st.error(
                f"Download failed: {exc}\n\n"
                "This can happen when:\n"
                "- Your session has expired — try logging out and back in\n"
                "- Zerodha's servers are temporarily busy — wait a moment and retry\n"
                "- The date range is too large for the selected interval"
            )
            return
        except PyZDataError as exc:
            st.error(f"Unexpected error: {exc}")
            return

    if df.empty:
        st.warning(
            f"No data was returned for **{symbol}** between {start_date} and {end_date}.\n\n"
            "Possible reasons:\n"
            "- This instrument doesn't trade on the selected dates (holiday, delisted, or not yet listed)\n"
            "- Try a shorter date range or a different interval"
        )
        return

    st.session_state["last_df"]   = df
    st.session_state["last_meta"] = {
        "symbol":    symbol,
        "exchange":  exchange,
        "interval":  freq_label or freq_label_for(interval),
        "start":     start_date,
        "end":       end_date,
    }
    st.balloons()
    st.rerun()


def freq_label_for(interval: Interval) -> str:
    for label, (iv, _) in FREQUENCY_OPTIONS.items():
        if iv == interval:
            return label.split("  ")[1].split("(")[0].strip()
    return interval.value


def _render_results(df: pd.DataFrame, meta: dict) -> None:
    symbol = meta.get("symbol", "Data")

    st.success(f"✅  Successfully downloaded **{len(df):,} rows** of data for **{symbol}**!")

    # ── Stats row ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Rows",  f"{len(df):,}")
    c2.metric("From",        str(df["datetime"].min().date()))
    c3.metric("To",          str(df["datetime"].max().date()))
    c4.metric("Highest",     f"₹{df['high'].max():,.2f}")
    c5.metric("Lowest",      f"₹{df['low'].min():,.2f}")
    c6.metric("Avg Volume",  f"{int(df['volume'].mean()):,}")

    # ── Price chart ────────────────────────────────────────────────────────
    st.markdown("#### Price Chart (Close)")
    chart_df = df.set_index("datetime")[["close"]].rename(columns={"close": "Close Price"})
    st.line_chart(chart_df, use_container_width=True)

    # ── Data table ─────────────────────────────────────────────────────────
    with st.expander(f"📋  Show data table ({len(df):,} rows)", expanded=False):
        st.dataframe(df, use_container_width=True, height=400)

    # ── Download buttons ───────────────────────────────────────────────────
    st.markdown("#### 💾  Save your data")

    fname_base = f"{symbol.replace(' ', '_')}_{df['datetime'].min().date()}_{df['datetime'].max().date()}"

    dl1, dl2, dl3 = st.columns([2, 2, 1])

    # CSV
    csv_data = df.to_csv(index=False).encode("utf-8")
    dl1.download_button(
        label="📄  Download as CSV",
        data=csv_data,
        file_name=f"{fname_base}.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
        help="Opens in Excel, Google Sheets, or any spreadsheet app.",
    )

    # Excel
    try:
        import io as _io

        import openpyxl  # noqa: F401 — only attempt if available
        buf = _io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=symbol[:31])
        buf.seek(0)
        dl2.download_button(
            label="📊  Download as Excel (.xlsx)",
            data=buf.getvalue(),
            file_name=f"{fname_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Native Excel format — preserves formatting.",
        )
    except ImportError:
        dl2.info("Install `openpyxl` for Excel export: `pip install openpyxl`")

    if dl3.button("🗑️  Clear", use_container_width=True):
        for k in ["last_df", "last_meta"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Search
# ─────────────────────────────────────────────────────────────────────────────

def render_search_tab() -> None:
    st.header("🔍  Find a stock or instrument")
    st.caption("Use this to discover the exact symbol name before downloading.")

    if not is_logged_in():
        st.info("Please log in using the sidebar first.")
        return

    client = get_client()

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input(
            "Search",
            placeholder="Type any part of the name — e.g.  HDFC,  NIFTY,  TATA",
            label_visibility="collapsed",
        )
    with col2:
        exch = st.selectbox("Exchange", ["All"] + EXCHANGES, label_visibility="collapsed")
    with col3:
        go = st.button("Search", type="primary", use_container_width=True)

    if go or query:
        if not query.strip():
            st.warning("Type something to search for.")
            return

        exchange_filter = None if exch == "All" else exch
        with st.spinner("Searching …"):
            results = client.search_instruments(query.strip(), exchange=exchange_filter)

        if results.empty:
            st.error(
                f"No instruments found matching **{query}**. "
                "Try a shorter search term or a different exchange."
            )
        else:
            st.success(f"Found **{len(results):,}** instrument(s) matching '{query}'.")

            display_cols = [c for c in
                ["tradingsymbol", "exchange", "instrument_type", "name",
                 "instrument_token", "expiry", "strike", "lot_size"]
                if c in results.columns]

            st.dataframe(results[display_cols], use_container_width=True, height=460)

            st.caption(
                "👆  Copy the **tradingsymbol** and **exchange** values from above, "
                "then paste them in the Download tab."
            )

            csv = results[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "Save search results as CSV",
                data=csv,
                file_name=f"search_{query.replace(' ', '_')}.csv",
                mime="text/csv",
            )


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — Help
# ─────────────────────────────────────────────────────────────────────────────

def render_help_tab() -> None:
    st.header("ℹ️  Help & FAQ")

    with st.expander("What is PyZData?", expanded=True):
        st.markdown("""
PyZData is a **free, open-source tool** for downloading historical Indian stock market
data directly from **Zerodha** (India's largest stockbroker).

It works with:
- **Stocks** — any company listed on NSE or BSE
- **Indices** — NIFTY 50, BANK NIFTY, SENSEX, etc.
- **Futures & Options (F&O)** — from the NSE F&O segment
- **Commodities** — from MCX

Data is returned in a table with columns: **Date/Time, Open, High, Low, Close, Volume**.
""")

    with st.expander("Do I need a paid Zerodha account?"):
        st.markdown("""
Yes — you need a **Zerodha trading account** to log in.

However, there is **no extra charge** for downloading historical data. It uses the
same Kite web platform you already have access to.

If you don't have a Zerodha account, you can open one at [zerodha.com](https://zerodha.com).
""")

    with st.expander("How do I get my enctoken?"):
        st.markdown("""
The enctoken is like a temporary password that proves you're logged into Kite.

**Steps:**
1. Open [kite.zerodha.com](https://kite.zerodha.com) and log in.
2. Press **F12** (Windows/Linux) or **Cmd+Option+I** (Mac) to open DevTools.
3. Click the **Application** tab → **Cookies** → **kite.zerodha.com**.
4. Find the row named **`enctoken`** and copy the value.

The enctoken is valid until you log out of Kite. If data stops downloading, get a fresh one.
""")

    with st.expander("What does each data frequency mean?"):
        for label, (_, desc) in FREQUENCY_OPTIONS.items():
            st.markdown(f"**{label}** — {desc}")

    with st.expander("What is Open Interest (OI)?"):
        st.markdown("""
Open Interest is the total number of outstanding F&O contracts that have not been settled.

- Only relevant for **Futures and Options** instruments (NFO, MCX)
- Has **no meaning** for regular stocks or indices
- Enable the OI option in Advanced Settings only when downloading F&O data
""")

    with st.expander("How far back can I download data?"):
        st.markdown("""
The Zerodha API allows the following maximum lookback periods:

| Interval | Maximum history |
|----------|----------------|
| Daily | Full history (many years) |
| 60 minutes | ~400 days |
| 30 minutes | ~400 days |
| 15 minutes | ~400 days |
| 5 minutes | ~100 days |
| 1 minute | ~60 days |

For longer history, use Daily candles.
""")

    with st.expander("Why does the symbol not work?"):
        st.markdown("""
Symbols are **case-sensitive** and must match exactly. Common issues:

| You typed | Correct symbol |
|-----------|---------------|
| NIFTY     | NIFTY 50      |
| BANKNIFTY | NIFTY BANK    |
| HDFC BANK | HDFCBANK      |
| INFOSY    | INFY          |

**Fix:** Use the **🔍 Search** tab to find the exact symbol name, then copy-paste it.
""")

    with st.expander("Is my data and password safe?"):
        st.markdown("""
- **Your password is never stored** — it is sent directly to Zerodha's login server.
- **Your enctoken is never stored** — it lives only in your browser session and disappears when you close the tab.
- This app has **no database** and makes **no outbound connections** other than to Zerodha's API.
- The complete source code is available on GitHub for independent review.
""")

    st.divider()
    st.markdown("""
**Still stuck?** Open an issue on GitHub:
[github.com/vikassharma545/Historical-Market-data-From-Zerodha](https://github.com/vikassharma545/Historical-Market-data-From-Zerodha)
""")


# ─────────────────────────────────────────────────────────────────────────────
# State initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_state() -> None:
    """Set default session-state values on the very first run."""
    defaults: dict = {
        "sym":        "",
        "exch":       "NSE",
        "start_date": date.today() - timedelta(days=365),
        "end_date":   date.today(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
/* ── hide Streamlit footer and main menu; keep header so users can
   access the built-in theme toggle (Settings → Theme) ── */
#MainMenu  { visibility: hidden; }
footer     { visibility: hidden; }

/* ── metric cards — rgba so they work in both light and dark mode ── */
[data-testid="metric-container"] {
    background: rgba(100, 116, 139, 0.08);
    border: 1px solid rgba(100, 116, 139, 0.25);
    border-radius: 12px;
    padding: 16px 12px;
}

/* ── rounded primary button ── */
.stButton > button[kind="primary"] {
    border-radius: 10px;
    font-size: 17px;
    font-weight: 600;
    padding: 12px 28px;
    background: #2563eb;
    border-color: #2563eb;
}
.stButton > button[kind="primary"]:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}

/* ── stock chip buttons ── */
div[data-testid="column"] .stButton > button {
    border-radius: 20px;
    font-size: 13px;
    padding: 6px 14px;
}

/* ── info banner — rgba background so text stays readable in dark mode ── */
.info-card {
    background: rgba(37, 99, 235, 0.10);
    border-left: 4px solid #2563eb;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.step-header {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 4px;
    margin-top: 24px;
}
</style>
"""


def main() -> None:
    # These two calls MUST stay inside main() so they run on every Streamlit
    # rerun (not just once when the module is first imported).
    st.set_page_config(
        page_title="PyZData – Stock Data Downloader",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    _init_state()
    render_sidebar()

    st.markdown("## 📊 PyZData — Indian Stock Market Data Downloader")

    if not is_logged_in():
        st.markdown("*Log in using the sidebar on the left to get started.*")
    else:
        st.markdown("*You are logged in. Pick a stock below and download.*")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📥  Download Data", "🔍  Search for a Stock", "ℹ️  Help"])

    with tab1:
        render_download_tab()
    with tab2:
        render_search_tab()
    with tab3:
        render_help_tab()


if __name__ == "__main__":
    main()
