"""Unit tests for InstrumentManager."""

import os
import time
from unittest.mock import MagicMock

import pytest
import requests

from pyzdata.config import Config
from pyzdata.exceptions import InstrumentNotFoundError
from pyzdata.instruments import InstrumentManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download_mock(session, csv_text: str):
    """Wire mock_session.get to return *csv_text* as a successful response."""
    resp = MagicMock(spec=requests.Response)
    resp.raise_for_status.return_value = None
    resp.text = csv_text
    session.get.return_value = resp
    return resp


def _loaded_manager(session, config, csv_text: str) -> InstrumentManager:
    _download_mock(session, csv_text)
    mgr = InstrumentManager(session, config)
    mgr.load()
    return mgr


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

class TestLoad:

    def test_downloads_when_cache_absent(self, mock_session, config, instruments_csv_text):
        _download_mock(mock_session, instruments_csv_text)
        mgr = InstrumentManager(mock_session, config)
        mgr.load()
        assert mock_session.get.called

    def test_writes_cache_after_download(self, mock_session, config, instruments_csv_text, tmp_path):
        cache = tmp_path / "inst.csv"
        config.instruments_cache_path = str(cache)
        config.instruments_cache_ttl_hours = 24
        _download_mock(mock_session, instruments_csv_text)
        mgr = InstrumentManager(mock_session, config)
        mgr.load()
        assert cache.exists()

    def test_uses_fresh_cache_without_download(self, mock_session, instruments_csv_text, tmp_path):
        cache = tmp_path / "inst.csv"
        cache.write_text(instruments_csv_text)
        cfg = Config(
            instruments_cache_path=str(cache),
            instruments_cache_ttl_hours=24,
        )
        mgr = InstrumentManager(mock_session, cfg)
        mgr.load()
        mock_session.get.assert_not_called()

    def test_redownloads_stale_cache(self, mock_session, instruments_csv_text, tmp_path):
        cache = tmp_path / "inst.csv"
        cache.write_text(instruments_csv_text)
        # Age the file to 48 hours ago
        old = time.time() - 48 * 3600
        os.utime(cache, (old, old))
        cfg = Config(
            instruments_cache_path=str(cache),
            instruments_cache_ttl_hours=24,
        )
        _download_mock(mock_session, instruments_csv_text)
        mgr = InstrumentManager(mock_session, cfg)
        mgr.load()
        assert mock_session.get.called


# ---------------------------------------------------------------------------
# get_token()
# ---------------------------------------------------------------------------

class TestGetToken:

    def test_known_symbol_returns_token(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        assert mgr.get_token("NIFTY 50", "NSE") == 256265
        assert mgr.get_token("RELIANCE", "NSE") == 408065

    def test_unknown_symbol_raises(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        with pytest.raises(InstrumentNotFoundError):
            mgr.get_token("DOES_NOT_EXIST", "NSE")

    def test_wrong_exchange_raises(self, mock_session, config, instruments_csv_text):
        """NIFTY 50 exists on NSE but not BSE in the fixture."""
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        with pytest.raises(InstrumentNotFoundError):
            mgr.get_token("NIFTY 50", "BSE")

    def test_returns_int(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        token = mgr.get_token("RELIANCE", "NSE")
        assert isinstance(token, int)


# ---------------------------------------------------------------------------
# get_symbol()
# ---------------------------------------------------------------------------

class TestGetSymbol:

    def test_known_token_returns_symbol(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        assert mgr.get_symbol(256265) == "NIFTY 50"

    def test_unknown_token_raises(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        with pytest.raises(InstrumentNotFoundError):
            mgr.get_symbol(9_999_999)


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

class TestSearch:

    def test_partial_match(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        result = mgr.search("NIFTY")
        # "NIFTY 50" and "NIFTY24JANFUT" should match
        assert len(result) == 2

    def test_case_insensitive(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        assert len(mgr.search("nifty")) == len(mgr.search("NIFTY"))

    def test_exchange_filter(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        result = mgr.search("NIFTY", exchange="NSE")
        assert len(result) == 1
        assert result.iloc[0]["exchange"] == "NSE"

    def test_no_match_returns_empty(self, mock_session, config, instruments_csv_text):
        mgr = _loaded_manager(mock_session, config, instruments_csv_text)
        result = mgr.search("ZZZNOTEXIST")
        assert result.empty


# ---------------------------------------------------------------------------
# _require_loaded()
# ---------------------------------------------------------------------------

class TestRequireLoaded:

    def test_raises_before_load(self, mock_session, config):
        mgr = InstrumentManager(mock_session, config)
        with pytest.raises(RuntimeError, match="not loaded"):
            mgr.get_token("X", "NSE")
