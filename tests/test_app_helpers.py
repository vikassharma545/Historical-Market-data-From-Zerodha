"""Tests for pure helper functions in pyzdata._app.

These tests do NOT require Streamlit or a running session — they exercise
only the logic that is free of UI side-effects.
"""

from pyzdata._app import (
    DATE_PRESETS,
    EXCHANGES,
    FREQUENCY_OPTIONS,
    POPULAR_STOCKS,
    _friendly_auth_error,
)
from pyzdata.models import Interval


# ── _friendly_auth_error ────────────────────────────────────────────────────


class TestFriendlyAuthError:
    def test_403_maps_to_wrong_credentials(self):
        assert "Wrong User ID or password" in _friendly_auth_error("HTTP 403 error")

    def test_password_keyword_maps_to_wrong_credentials(self):
        assert "Wrong User ID or password" in _friendly_auth_error("bad password")

    def test_totp_maps_to_wrong_totp(self):
        assert "TOTP" in _friendly_auth_error("Invalid totp code")

    def test_2fa_maps_to_wrong_totp(self):
        assert "TOTP" in _friendly_auth_error("2FA rejected by server")

    def test_twofa_maps_to_wrong_totp(self):
        assert "TOTP" in _friendly_auth_error("twofa failed")

    def test_enctoken_maps_to_expired_token(self):
        assert "expired enctoken" in _friendly_auth_error("enctoken invalid")

    def test_network_error(self):
        assert "Network error" in _friendly_auth_error("Network timeout occurred")

    def test_connection_error(self):
        assert "Network error" in _friendly_auth_error("Could not connect to server")

    def test_unknown_error_returned_as_is(self):
        msg = "Something completely unexpected happened"
        assert _friendly_auth_error(msg) == msg


# ── Data table integrity ────────────────────────────────────────────────────


class TestDataTables:
    def test_popular_stocks_have_four_fields(self):
        for entry in POPULAR_STOCKS:
            assert len(entry) == 4, f"Expected 4 fields, got {len(entry)}: {entry}"

    def test_popular_stocks_exchanges_are_valid(self):
        for symbol, exchange, label, emoji in POPULAR_STOCKS:
            assert exchange in EXCHANGES, f"{symbol} has invalid exchange {exchange}"

    def test_frequency_options_map_to_valid_intervals(self):
        valid_intervals = set(Interval)
        for label, (interval, desc) in FREQUENCY_OPTIONS.items():
            assert interval in valid_intervals, f"{label} maps to unknown Interval"
            assert isinstance(desc, str) and len(desc) > 0

    def test_date_presets_are_positive_days(self):
        for label, days in DATE_PRESETS.items():
            assert isinstance(days, int) and days > 0, f"{label}: {days}"

    def test_date_presets_are_ascending(self):
        values = list(DATE_PRESETS.values())
        assert values == sorted(values), "DATE_PRESETS should be in ascending order"
