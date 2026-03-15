"""Command-line interface for PyZData.

Installed as the ``pyzdata`` console script via ``pyproject.toml``.

Usage examples::

    # Day candles via enctoken
    pyzdata --enctoken TOKEN "NIFTY 50" NSE 2024-01-01 2024-12-31 --interval day

    # Minute candles with credentials, save to CSV
    pyzdata --user-id AB1234 --password pw --totp 123456 \\
        RELIANCE NSE 2024-01-01 2024-06-30 --interval minute --output data.csv

    # F&O instrument with open interest
    pyzdata --enctoken TOKEN NIFTY24JANFUT NFO 2024-01-01 2024-01-25 --oi

    # Search for available symbols
    pyzdata --enctoken TOKEN search NIFTY --exchange NSE
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import NoReturn

from . import Config, Interval, PyZData
from .exceptions import PyZDataError


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyzdata",
        description="Download historical OHLCV data from Zerodha (Kite API).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  pyzdata --enctoken TOKEN "NIFTY 50" NSE 2024-01-01 2024-12-31
  pyzdata --enctoken TOKEN RELIANCE NSE 2024-01-01 2024-06-30 --interval minute -o out.csv
  pyzdata --user-id AB1234 --password pw --totp 123456 RELIANCE NSE 2024-01-01 2024-01-31
""",
    )

    # ---------- authentication (mutually exclusive) ----------
    auth = p.add_mutually_exclusive_group(required=True)
    auth.add_argument("--enctoken", metavar="TOKEN",  help="Zerodha enctoken")
    auth.add_argument("--user-id",  metavar="ID",     help="Zerodha user ID")

    p.add_argument("--password", metavar="PW",   help="Password  (required with --user-id)")
    p.add_argument("--totp",     metavar="CODE", help="TOTP code (required with --user-id)")

    # ---------- data parameters ----------
    sub = p.add_subparsers(dest="command")

    # ---- download (default) ----
    dl = sub.add_parser("download", help="Download historical data (default)")
    _add_download_args(dl)

    # ---- search ----
    sr = sub.add_parser("search", help="Search for instrument symbols")
    sr.add_argument("query", help="Symbol search term, e.g. NIFTY")
    sr.add_argument("--exchange", "-e", help="Filter by exchange (NSE, BSE, NFO …)")

    # Positional args on the root parser act as the implicit 'download' command
    _add_download_args(p)

    # ---------- global flags ----------
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    return p


def _add_download_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("symbol",   nargs="?", help="Trading symbol, e.g. 'NIFTY 50'")
    parser.add_argument("exchange", nargs="?", help="Exchange: NSE, BSE, NFO, MCX …")
    parser.add_argument("start",    nargs="?", metavar="START_DATE", help="Start date YYYY-MM-DD")
    parser.add_argument("end",      nargs="?", metavar="END_DATE",   help="End date YYYY-MM-DD")
    parser.add_argument(
        "--interval", "-i",
        default="day",
        choices=[i.value for i in Interval],
        metavar="INTERVAL",
        help=(
            "Candle interval. Choices: "
            + ", ".join(i.value for i in Interval)
            + " (default: day)"
        ),
    )
    parser.add_argument("--oi",     action="store_true", help="Include open interest column")
    parser.add_argument("--output", "-o", metavar="FILE", help="Save to CSV (default: print to stdout)")


def main() -> None:  # noqa: C901
    parser = _build_parser()
    args   = parser.parse_args()

    # ---------- logging ----------
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---------- auth validation ----------
    if args.user_id and not (args.password and args.totp):
        parser.error("--password and --totp are required when using --user-id")

    try:
        client = _build_client(args)

        # ---------- search sub-command ----------
        if getattr(args, "command", None) == "search":
            results = client.search_instruments(
                args.query, exchange=getattr(args, "exchange", None)
            )
            if results.empty:
                print("No instruments found.", file=sys.stderr)
                sys.exit(1)
            print(results.to_string(index=False))
            return

        # ---------- download ----------
        if not all([args.symbol, args.exchange, args.start, args.end]):
            parser.error(
                "symbol, exchange, START_DATE and END_DATE are required for download. "
                "Run 'pyzdata --help' for usage."
            )

        interval = next(i for i in Interval if i.value == args.interval)
        token    = client.get_instrument_token(args.symbol, args.exchange)
        df       = client.get_data(token, args.start, args.end, interval, oi=args.oi)

        if df.empty:
            print("No data returned for the specified parameters.", file=sys.stderr)
            sys.exit(1)

        if args.output:
            df.to_csv(args.output, index=False)
            print(f"Saved {len(df):,} rows to {args.output}")
        else:
            print(df.to_string())

    except PyZDataError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)


def _build_client(args: argparse.Namespace) -> PyZData:
    if args.enctoken:
        return PyZData(enctoken=args.enctoken)
    return PyZData(user_id=args.user_id, password=args.password, totp=args.totp)
