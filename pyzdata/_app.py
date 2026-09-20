"""PyZData web interface — one page: log in, pick, download.

Run with:
    pyzdata-web            (installed)
    streamlit run app.py   (from a checkout)

Only Streamlit calls live here.  Tables and pure logic are in
:mod:`pyzdata._web_helpers` so they can be tested without a browser.
"""

from __future__ import annotations

import importlib.util
import io
import math
from datetime import date, timedelta
from typing import Callable, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from pyzdata import Config, Interval, PyZData, __version__
from pyzdata._web_helpers import (
    DERIVATIVE_EXCHANGES,
    EXCEL_MAX_ROWS,
    EXCHANGE_HELP,
    EXCHANGES,
    INTERVALS,
    MAIN_INTERVALS,
    PERIODS,
    chart_frame,
    contract_options,
    file_stem,
    friendly_error,
    instrument_options,
    period_to_dates,
    to_excel_bytes,
    underlyings,
)
from pyzdata.downloader import _max_days
from pyzdata.exceptions import (
    AuthenticationError,
    DataFetchError,
    PartialDataError,
    PyZDataError,
)

_REPO_URL = "https://github.com/vikassharma545/Historical-Market-data-From-Zerodha"
_DEFAULT_PERIOD = "1Y"
_OTHER = "Other"
_CUSTOM = "Custom"

_ENCTOKEN_GUIDE = """
1. Open [kite.zerodha.com](https://kite.zerodha.com) and log in as usual.
2. Press **F12** (Mac: **Cmd + Option + I**) to open Developer Tools.
3. Open the **Application** tab (Firefox: **Storage**) → **Cookies** → `kite.zerodha.com`.
4. Copy the value of the cookie named **`enctoken`** and paste it here.

The enctoken changes every time you log in to Kite. If it stops working, copy a fresh one.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

def render_login() -> None:
    st.title("📊 PyZData")
    st.markdown(
        "Download historical prices for any stock, index, future or option on "
        "Zerodha — as CSV or Excel. Free, no API subscription."
    )

    method = st.segmented_control(
        "Log in with",
        ["Enctoken", "User ID & password"],
        default="Enctoken",
        key="login_method",
    ) or "Enctoken"

    # A form, so pressing Enter submits and typing doesn't rerun the page.
    with st.form("login"):
        if method == "Enctoken":
            credentials = {
                "enctoken": st.text_input(
                    "Enctoken", type="password", placeholder="Paste your enctoken",
                ),
            }
        else:
            credentials = {
                "user_id": st.text_input("Zerodha user ID", placeholder="AB1234"),
                "password": st.text_input("Password", type="password"),
                "totp": st.text_input(
                    "TOTP code", max_chars=6, placeholder="6 digits from your authenticator app",
                ),
            }
        submitted = st.form_submit_button("Log in", type="primary", width="stretch")

    if submitted:
        credentials = {name: value.strip() for name, value in credentials.items()}
        if all(credentials.values()):
            _log_in(credentials)
        else:
            st.error("Please fill in every field.")

    with st.expander("How do I get my enctoken?"):
        st.markdown(_ENCTOKEN_GUIDE)
    with st.expander("Is this safe?"):
        st.markdown(
            "- Your login details go **only to Zerodha's servers**, straight from this computer.\n"
            "- Nothing is written to disk — the session ends when you close this tab.\n"
            f"- The code is open source: [read it on GitHub]({_REPO_URL})."
        )


def _log_in(credentials: Dict[str, str]) -> None:
    try:
        with st.spinner("Connecting to Zerodha …"):
            client = PyZData(config=Config.from_env(), **credentials)
    except AuthenticationError as exc:
        st.error(friendly_error(str(exc)))
    except PyZDataError as exc:
        st.error(f"Could not log in: {exc}")
    else:
        st.session_state["client"] = client
        st.rerun()


def _log_out() -> None:
    client = st.session_state.get("client")
    if client is not None:
        client.close()
    st.session_state.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Pickers
# ─────────────────────────────────────────────────────────────────────────────

def _cached(key: Tuple[str, ...], build: Callable[[], object]) -> object:
    """Per-session memo — option lists are built from a ~100k-row table."""
    cache = st.session_state.setdefault("_options", {})
    if key not in cache:
        cache[key] = build()
    return cache[key]


def _pick_instrument(client: PyZData) -> Tuple[str, Optional[str]]:
    exchange = st.segmented_control(
        "Exchange", EXCHANGES, default="NSE", key="exchange", help=EXCHANGE_HELP,
    ) or "NSE"
    instruments = client.instruments

    if exchange not in DERIVATIVE_EXCHANGES:
        options = _cached(("cash", exchange), lambda: instrument_options(instruments, exchange))
        symbol = st.selectbox(
            "Stock or index",
            list(options),
            index=None,
            format_func=options.get,
            placeholder="Type to search — e.g. RELIANCE, NIFTY 50, TCS",
            key=f"symbol_{exchange}",
        )
        return exchange, symbol

    names = _cached(("underlyings", exchange), lambda: underlyings(instruments, exchange))
    left, right = st.columns(2)
    underlying = left.selectbox(
        "Underlying",
        names,
        index=None,
        placeholder="Type to search — e.g. NIFTY, CRUDEOIL",
        key=f"underlying_{exchange}",
    )
    options = (
        _cached(
            ("contracts", exchange, underlying),
            lambda: contract_options(instruments, exchange, underlying),
        )
        if underlying
        else {}
    )
    symbol = right.selectbox(
        "Contract",
        list(options),
        index=None,
        format_func=options.get,
        placeholder="Choose a contract" if underlying else "Pick an underlying first",
        disabled=not underlying,
        key=f"contract_{exchange}_{underlying}",
    )
    return exchange, symbol


def _pick_dates() -> Optional[Tuple[date, date]]:
    today = date.today()
    period = st.pills(
        "Period", list(PERIODS) + [_CUSTOM], default=_DEFAULT_PERIOD, key="period",
    ) or _DEFAULT_PERIOD

    if period != _CUSTOM:
        start, end = period_to_dates(period, today)
        st.caption(f"{start:%d %b %Y} → {end:%d %b %Y}")
        return start, end

    left, right = st.columns(2)
    start = left.date_input("From", value=today - timedelta(days=365), max_value=today)
    end = right.date_input("To", value=today, max_value=today)
    if start > end:
        st.error("The From date must be on or before the To date.")
        return None
    return start, end


def _pick_interval() -> Tuple[str, Interval]:
    choice = st.pills(
        "Candle interval", MAIN_INTERVALS + [_OTHER], default=MAIN_INTERVALS[0], key="interval",
    ) or MAIN_INTERVALS[0]
    if choice == _OTHER:
        choice = st.selectbox(
            "Other interval",
            [label for label in INTERVALS if label not in MAIN_INTERVALS],
            label_visibility="collapsed",
        )
    return choice, INTERVALS[choice]


# ─────────────────────────────────────────────────────────────────────────────
# Download
# ─────────────────────────────────────────────────────────────────────────────

def render_downloader(client: PyZData) -> None:
    title, account = st.columns([3, 1], vertical_alignment="bottom")
    title.title("📊 PyZData")
    account.button("Log out", on_click=_log_out, width="stretch")
    st.caption(f"Logged in as **{client.user_name or 'Zerodha user'}**")

    exchange, symbol = _pick_instrument(client)
    dates = _pick_dates()
    interval_label, interval = _pick_interval()

    with_oi = False
    if exchange in DERIVATIVE_EXCHANGES:
        with_oi = st.checkbox(
            "Include open interest", value=True,
            help="Adds an open_interest column — the number of outstanding contracts.",
        )

    if dates:
        requests_needed = math.ceil(((dates[1] - dates[0]).days + 1) / _max_days(interval))
        if requests_needed > 10:
            st.caption(
                f"This needs about {requests_needed} requests to Zerodha — "
                "a shorter period or a longer interval is quicker."
            )

    clicked = st.button(
        f"Download {symbol}" if symbol else "Pick an instrument to download",
        type="primary",
        width="stretch",
        disabled=not (symbol and dates),
    )
    if clicked:
        _download(client, symbol, exchange, dates, interval_label, interval, with_oi)

    if "result" in st.session_state:
        _render_result(st.session_state["result"])


def _download(
    client: PyZData,
    symbol: str,
    exchange: str,
    dates: Tuple[date, date],
    interval_label: str,
    interval: Interval,
    with_oi: bool,
) -> None:
    st.session_state.pop("result", None)
    bar = st.progress(0.0, text=f"Downloading {symbol} …")

    def on_progress(done: int, total: int) -> None:
        bar.progress(done / total, text=f"Downloading {symbol} … part {done} of {total}")

    warning = None
    try:
        token = client.get_instrument_token(symbol, exchange)
        df = client.get_data(
            token, str(dates[0]), str(dates[1]), interval,
            oi=with_oi, progress_callback=on_progress,
        )
    except PartialDataError as exc:
        df = exc.partial_data
        gaps = ", ".join(f"{start:%d %b %Y} → {end:%d %b %Y}" for start, end in exc.failed_ranges)
        warning = (
            f"Some of the data could not be downloaded and is **missing** from the "
            f"file: {gaps}. Click Download again to retry."
        )
    except DataFetchError as exc:
        bar.empty()
        if "expired" in str(exc):
            st.error("Your Zerodha session has expired. Log out, then log in again.")
        else:
            st.error(f"Download failed: {exc}. Wait a moment and try again.")
        return
    except PyZDataError as exc:
        bar.empty()
        st.error(str(exc))
        return
    bar.empty()

    if df.empty:
        st.warning(
            f"Zerodha has no {interval_label.lower()} data for **{symbol}** in this period. "
            "It may not have been listed yet — try a different period."
        )
        return

    # Keep only bytes and small frames: Streamlit holds session state in
    # memory for the whole session, and a 1-minute download can be huge.
    st.session_state["result"] = {
        "title": f"{symbol} · {interval_label}",
        "rows": len(df),
        "first": df["datetime"].min(),
        "last": df["datetime"].max(),
        "last_close": float(df["close"].iloc[-1]),
        "stem": file_stem(symbol, df, interval_label),
        "csv": df.to_csv(index=False).encode("utf-8"),
        "chart": chart_frame(df),
        "preview": df.head(10),
        "warning": warning,
    }


def _render_result(result: dict) -> None:
    st.divider()
    st.subheader(result["title"])
    if result["warning"]:
        st.warning(result["warning"])

    rows, span, close = st.columns([1, 2, 1])
    rows.metric("Rows", f"{result['rows']:,}")
    span.metric("Period", f"{result['first']:%d %b %Y} → {result['last']:%d %b %Y}")
    close.metric("Last close", f"{result['last_close']:,.2f}")

    st.line_chart(result["chart"], height=260)

    csv = result["csv"]
    left, right = st.columns(2)
    left.download_button(
        "Save as CSV", csv, file_name=f"{result['stem']}.csv", mime="text/csv",
        type="primary", width="stretch",
    )
    if importlib.util.find_spec("openpyxl") is not None:
        too_big = result["rows"] > EXCEL_MAX_ROWS
        right.download_button(
            "Save as Excel",
            # Built only when clicked — writing a big workbook takes a while.
            lambda: to_excel_bytes(pd.read_csv(io.BytesIO(csv), parse_dates=["datetime"])),
            file_name=f"{result['stem']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            disabled=too_big,
            help="Excel can't hold more than 1,048,575 rows — use CSV." if too_big else None,
        )

    with st.expander("Preview the first rows"):
        st.dataframe(result["preview"], hide_index=True, width="stretch")


# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

def render_help() -> None:
    st.divider()
    with st.expander("Help"):
        st.markdown(f"""
**What do I get?** One row per candle: `tradingsymbol, datetime, open, high, low, close,
volume` (plus `open_interest` for futures & options). Times are in IST.

**Which interval should I pick?** *Day* for long-term trends and backtests; *1 hour* to
*15 min* for swing trading; *5 min* and *1 min* for intraday work. Shorter intervals make
much bigger files and take longer to download.

**I can't find my instrument.** Check the exchange first — shares and indices are on
NSE / BSE, futures & options on NFO / BFO, commodities on MCX, currency on CDS. Then type
part of the name in the dropdown. Expired contracts are not available from Zerodha.

**What is open interest?** The number of futures or options contracts still open. It only
exists for derivatives, so the option appears only on those exchanges.

**The download says my session expired.** Zerodha ends a session when you log in to Kite
somewhere else. Log out here and log in again with a fresh enctoken.

**Do I need to pay?** No. You need a Zerodha account, but not the paid Kite Connect API.

Still stuck? [Open an issue on GitHub]({_REPO_URL}/issues). &nbsp; · &nbsp; PyZData v{__version__}
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="PyZData — market data downloader", page_icon="📊")

    client = st.session_state.get("client")
    if client is None:
        render_login()
    else:
        render_downloader(client)
    render_help()


if __name__ == "__main__":
    main()
