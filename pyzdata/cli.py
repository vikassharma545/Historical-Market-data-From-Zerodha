"""Command-line interface for PyZData.

Installed as the ``pyzdata`` console script via ``pyproject.toml``.

Usage examples::

    # Day candles via enctoken
    pyzdata download --enctoken TOKEN --symbol "NIFTY 50" --exchange NSE \\
        --start 2024-01-01 --end 2024-12-31

    # Minute candles with credentials, save to CSV
    pyzdata download --user-id AB1234 --password pw --totp 123456 \\
        --symbol RELIANCE --exchange NSE --start 2024-01-01 --end 2024-06-30 \\
        --interval minute --output data.csv

    # F&O instrument with open interest
    pyzdata download --enctoken TOKEN --symbol NIFTY24JANFUT --exchange NFO \\
        --start 2024-01-01 --end 2024-01-25 --oi

    # Search for available symbols
    pyzdata search --enctoken TOKEN --query NIFTY --exchange NSE
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import Interval, PyZData
from .exceptions import PyZDataError


def _add_auth_args(parser: argparse.ArgumentParser) -> None:
    """Add authentication flags to a parser."""
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--enctoken", metavar="TOKEN", help="Zerodha enctoken")
    auth.add_argument("--user-id", metavar="ID", help="Zerodha user ID")
    parser.add_argument("--password", metavar="PW", help="Password (required with --user-id)")
    parser.add_argument("--totp", metavar="CODE", help="TOTP code (required with --user-id)")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyzdata",
        description="Download historical OHLCV data from Zerodha (Kite API).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  pyzdata download --enctoken TOKEN --symbol "NIFTY 50" --exchange NSE --start 2024-01-01 --end 2024-12-31
  pyzdata download --enctoken TOKEN --symbol RELIANCE --exchange NSE --start 2024-01-01 --end 2024-06-30 --interval minute -o out.csv
  pyzdata search --enctoken TOKEN --query NIFTY --exchange NSE
""",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # ---- download ----
    dl = sub.add_parser(
        "download",
        help="Download historical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_auth_args(dl)
    dl.add_argument("--symbol",   "-s", required=True, help="Trading symbol, e.g. 'NIFTY 50'")
    dl.add_argument("--exchange", "-e", required=True, help="Exchange: NSE, BSE, NFO, MCX …")
    dl.add_argument("--start",          required=True, metavar="START_DATE", help="Start date YYYY-MM-DD")
    dl.add_argument("--end",            required=True, metavar="END_DATE",   help="End date YYYY-MM-DD")
    dl.add_argument(
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
    dl.add_argument("--oi",     action="store_true", help="Include open interest column")
    dl.add_argument("--output", "-o", metavar="FILE", help="Save to CSV (default: print to stdout)")

    # ---- search ----
    sr = sub.add_parser(
        "search",
        help="Search for instrument symbols",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_auth_args(sr)
    sr.add_argument("--query", "-q", required=True, help="Symbol search term, e.g. NIFTY")
    sr.add_argument("--exchange", "-e", help="Filter by exchange (NSE, BSE, NFO …)")

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ---------- logging ----------
    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---------- auth validation ----------
    if getattr(args, "user_id", None) and not (
        getattr(args, "password", None) and getattr(args, "totp", None)
    ):
        parser.error("--password and --totp are required when using --user-id")

    try:
        client = _build_client(args)

        if args.command == "search":
            _handle_search(client, args)
        else:
            _handle_download(client, args)

    except PyZDataError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)


def _handle_search(client: PyZData, args: argparse.Namespace) -> None:
    results = client.search_instruments(
        args.query, exchange=getattr(args, "exchange", None)
    )
    if results.empty:
        print("No instruments found.", file=sys.stderr)
        sys.exit(1)
    print(results.to_string(index=False))


def _handle_download(client: PyZData, args: argparse.Namespace) -> None:
    interval = next(i for i in Interval if i.value == args.interval)
    token = client.get_instrument_token(args.symbol, args.exchange)
    df = client.get_data(token, args.start, args.end, interval, oi=args.oi)

    if df.empty:
        print("No data returned for the specified parameters.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved {len(df):,} rows to {args.output}")
    else:
        print(df.to_string())


def _build_client(args: argparse.Namespace) -> PyZData:
    if getattr(args, "enctoken", None):
        return PyZData(enctoken=args.enctoken)
    return PyZData(user_id=args.user_id, password=args.password, totp=args.totp)
