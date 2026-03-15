"""Unit tests for Config and Config.from_env()."""

import os
from unittest.mock import patch

import pytest

from pyzdata.config import Config


class TestConfigDefaults:

    def test_default_values(self):
        cfg = Config()
        assert cfg.max_retries == 5
        assert cfg.backoff_factor == 1.0
        assert cfg.request_timeout == 30
        assert cfg.max_workers == 4
        assert cfg.instruments_cache_ttl_hours == 24.0
        assert cfg.instruments_cache_path is None
        assert cfg.log_level == "WARNING"

    def test_default_urls(self):
        cfg = Config()
        assert "kite.zerodha.com" in cfg.root_url
        assert "kite.zerodha.com" in cfg.login_url
        assert "kite.zerodha.com" in cfg.twofa_url
        assert "kite.trade" in cfg.instruments_url

    def test_retry_status_codes(self):
        cfg = Config()
        assert 429 in cfg.retry_status_codes
        assert 500 in cfg.retry_status_codes
        assert 502 in cfg.retry_status_codes
        assert 503 in cfg.retry_status_codes
        assert 504 in cfg.retry_status_codes

    def test_custom_values(self):
        cfg = Config(max_retries=10, max_workers=16, log_level="DEBUG")
        assert cfg.max_retries == 10
        assert cfg.max_workers == 16
        assert cfg.log_level == "DEBUG"


class TestConfigFromEnv:

    def test_reads_max_retries_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_MAX_RETRIES": "10"}):
            cfg = Config.from_env()
            assert cfg.max_retries == 10

    def test_reads_max_workers_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_MAX_WORKERS": "16"}):
            cfg = Config.from_env()
            assert cfg.max_workers == 16

    def test_reads_timeout_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_TIMEOUT": "60"}):
            cfg = Config.from_env()
            assert cfg.request_timeout == 60

    def test_reads_backoff_factor_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_BACKOFF_FACTOR": "2.5"}):
            cfg = Config.from_env()
            assert cfg.backoff_factor == 2.5

    def test_reads_cache_ttl_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_CACHE_TTL_HOURS": "48"}):
            cfg = Config.from_env()
            assert cfg.instruments_cache_ttl_hours == 48.0

    def test_reads_cache_path_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_CACHE_PATH": "/custom/path.csv"}):
            cfg = Config.from_env()
            assert cfg.instruments_cache_path == "/custom/path.csv"

    def test_reads_log_level_from_env(self):
        with patch.dict(os.environ, {"PYZDATA_LOG_LEVEL": "debug"}):
            cfg = Config.from_env()
            assert cfg.log_level == "DEBUG"  # uppercased

    def test_empty_cache_path_becomes_none(self):
        with patch.dict(os.environ, {"PYZDATA_CACHE_PATH": ""}):
            cfg = Config.from_env()
            assert cfg.instruments_cache_path is None

    def test_defaults_when_env_unset(self):
        """Ensure from_env() uses defaults when no PYZDATA_* vars are set."""
        clean = {k: v for k, v in os.environ.items() if not k.startswith("PYZDATA_")}
        with patch.dict(os.environ, clean, clear=True):
            cfg = Config.from_env()
            assert cfg.max_retries == 5
            assert cfg.max_workers == 4
            assert cfg.log_level == "WARNING"
