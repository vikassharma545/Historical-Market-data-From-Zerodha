"""Tests for the _Throttle rate limiter in pyzdata.downloader."""

import time

from pyzdata.downloader import _Throttle


class TestThrottle:
    def test_zero_rate_does_not_sleep(self):
        """rate_limit_per_second=0 disables throttling entirely."""
        throttle = _Throttle(0)
        start = time.monotonic()
        for _ in range(5):
            throttle.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05, f"Expected instant, took {elapsed:.3f}s"

    def test_throttle_enforces_minimum_gap(self):
        """With 5 req/s, 3 calls should take at least ~0.4s total gap."""
        throttle = _Throttle(5.0)  # 200ms between calls
        start = time.monotonic()
        for _ in range(3):
            throttle.wait()
        elapsed = time.monotonic() - start
        # 2 gaps of ~200ms = ~400ms minimum
        assert elapsed >= 0.35, f"Expected >= 0.35s, got {elapsed:.3f}s"

    def test_negative_rate_does_not_sleep(self):
        """Negative values should behave like disabled throttle."""
        throttle = _Throttle(-1)
        start = time.monotonic()
        throttle.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05
