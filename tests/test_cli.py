"""Unit tests for the CLI argument parser and main() error paths."""

from unittest.mock import patch

import pytest

from pyzdata.cli import _build_parser, main


class TestBuildParser:

    def _parse(self, args_list):
        """Parse args via the CLI parser."""
        parser = _build_parser()
        return parser.parse_args(args_list)

    def test_download_with_enctoken(self):
        args = self._parse([
            "download",
            "--enctoken", "TOKEN",
            "--symbol", "RELIANCE",
            "--exchange", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-06-30",
        ])
        assert args.command == "download"
        assert args.enctoken == "TOKEN"
        assert args.symbol == "RELIANCE"
        assert args.exchange == "NSE"
        assert args.start == "2024-01-01"
        assert args.end == "2024-06-30"

    def test_download_with_user_id(self):
        args = self._parse([
            "download",
            "--user-id", "AB1234",
            "--password", "secret",
            "--totp", "123456",
            "--symbol", "NIFTY 50",
            "--exchange", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-12-31",
        ])
        assert args.user_id == "AB1234"
        assert args.password == "secret"
        assert args.totp == "123456"
        assert args.symbol == "NIFTY 50"

    def test_default_interval_is_day(self):
        args = self._parse([
            "download",
            "--enctoken", "TOKEN",
            "-s", "RELIANCE",
            "-e", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-06-30",
        ])
        assert args.interval == "day"

    def test_custom_interval(self):
        args = self._parse([
            "download",
            "--enctoken", "TOKEN",
            "-s", "RELIANCE",
            "-e", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-06-30",
            "--interval", "minute",
        ])
        assert args.interval == "minute"

    def test_oi_flag(self):
        args = self._parse([
            "download",
            "--enctoken", "TOKEN",
            "-s", "RELIANCE",
            "-e", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-06-30",
            "--oi",
        ])
        assert args.oi is True

    def test_output_flag(self):
        args = self._parse([
            "download",
            "--enctoken", "TOKEN",
            "-s", "RELIANCE",
            "-e", "NSE",
            "--start", "2024-01-01",
            "--end", "2024-06-30",
            "-o", "data.csv",
        ])
        assert args.output == "data.csv"

    def test_search_subcommand(self):
        args = self._parse([
            "search",
            "--enctoken", "TOKEN",
            "--query", "NIFTY",
            "--exchange", "NSE",
        ])
        assert args.command == "search"
        assert args.query == "NIFTY"
        assert args.exchange == "NSE"

    def test_search_short_flags(self):
        args = self._parse([
            "search",
            "--enctoken", "TOKEN",
            "-q", "HDFC",
        ])
        assert args.query == "HDFC"

    def test_no_subcommand_raises(self):
        """A subcommand is required."""
        with pytest.raises(SystemExit):
            self._parse(["--enctoken", "TOKEN"])

    def test_no_auth_raises(self):
        """Missing auth in download subcommand should fail."""
        with pytest.raises(SystemExit):
            self._parse([
                "download",
                "-s", "RELIANCE",
                "-e", "NSE",
                "--start", "2024-01-01",
                "--end", "2024-06-30",
            ])


class TestMainErrorPaths:

    _DOWNLOAD_ARGS = [
        "pyzdata", "download",
        "--enctoken", "TOKEN",
        "-s", "RELIANCE", "-e", "NSE",
        "--start", "2024-01-01", "--end", "2024-06-30",
    ]

    @patch("pyzdata.cli._build_client")
    @patch("sys.argv", _DOWNLOAD_ARGS)
    def test_pyzdata_error_exits_1(self, mock_build):
        from pyzdata.exceptions import PyZDataError
        mock_build.side_effect = PyZDataError("test error")
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("pyzdata.cli._build_client")
    @patch("sys.argv", _DOWNLOAD_ARGS)
    def test_keyboard_interrupt_exits_130(self, mock_build):
        mock_build.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 130
