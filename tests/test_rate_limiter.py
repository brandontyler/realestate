"""Unit tests for mls/rate_limiter.py — 100% coverage target."""

import time
from unittest.mock import patch

import pytest

from mls.rate_limiter import QuotaBucket, RateLimiter, _parse_iso


# ── _parse_iso ──────────────────────────────────────────────────────────────

class TestParseIso:
    def test_utc_z_suffix(self):
        ts = _parse_iso("2026-03-10T20:54:31.983Z")
        assert ts > 0
        # Just verify it parses to a reasonable epoch (March 2026)
        assert 1773000000 < ts < 1774000000

    def test_offset_suffix(self):
        ts = _parse_iso("2026-03-10T15:54:31.983-05:00")
        assert ts > 0

    def test_invalid_string(self):
        assert _parse_iso("not-a-date") == 0.0

    def test_none_input(self):
        assert _parse_iso(None) == 0.0


# ── QuotaBucket ─────────────────────────────────────────────────────────────

class TestQuotaBucket:
    def test_defaults(self):
        b = QuotaBucket()
        assert b.limit == 0
        assert b.remaining == 0
        assert b.reset_time == 0.0


# ── RateLimiter.update_from_bridge ──────────────────────────────────────────

class TestBridgeHeaders:
    def test_full_headers(self):
        rl = RateLimiter()
        rl.update_from_bridge({
            "application-ratelimit-limit": "5000",
            "application-ratelimit-remaining": "4990",
            "application-ratelimit-reset": "2026-03-10T21:00:00Z",
            "burst-ratelimit-limit": "334",
            "burst-ratelimit-remaining": "330",
            "burst-ratelimit-reset": "2026-03-10T20:15:00Z",
        })
        assert rl.hourly.limit == 5000
        assert rl.hourly.remaining == 4990
        assert rl.hourly.reset_time > 0
        assert rl.burst.limit == 334
        assert rl.burst.remaining == 330
        assert rl.burst.reset_time > 0

    def test_partial_headers(self):
        rl = RateLimiter()
        rl.update_from_bridge({"application-ratelimit-limit": "5000"})
        assert rl.hourly.limit == 5000
        assert rl.hourly.remaining == 0  # not set

    def test_empty_headers(self):
        rl = RateLimiter()
        rl.update_from_bridge({})
        assert rl.hourly.limit == 0


# ── RateLimiter.update_from_trestle ─────────────────────────────────────────

class TestTrestleHeaders:
    def test_first_call_seeds_remaining(self):
        rl = RateLimiter()
        rl.update_from_trestle({
            "Hour-Quota-Limit": "7200.0",
            "Minute-Quota-Limit": "180.0",
            "Hour-Quota-ResetTime": "1773357271000",
        })
        assert rl.hourly.limit == 7200
        assert rl.hourly.remaining == 7200
        assert rl.burst.limit == 180
        assert rl.burst.remaining == 180

    def test_subsequent_calls_dont_reset_remaining(self):
        rl = RateLimiter()
        # First call
        rl.update_from_trestle({
            "Hour-Quota-Limit": "7200.0",
            "Minute-Quota-Limit": "180.0",
            "Hour-Quota-ResetTime": "1773357271000",
        })
        # Simulate consumption
        rl.hourly.remaining = 7100
        rl.burst.remaining = 170
        # Second call — same reset time
        rl.update_from_trestle({
            "Hour-Quota-Limit": "7200.0",
            "Minute-Quota-Limit": "180.0",
            "Hour-Quota-ResetTime": "1773357271000",
        })
        assert rl.hourly.remaining == 7100  # NOT reset to 7200
        assert rl.burst.remaining == 170

    def test_reset_time_change_refills_hourly(self):
        rl = RateLimiter()
        rl.update_from_trestle({
            "Hour-Quota-Limit": "7200.0",
            "Hour-Quota-ResetTime": "1773357271000",
        })
        rl.hourly.remaining = 100
        # New reset time = quota window rolled over
        rl.update_from_trestle({
            "Hour-Quota-Limit": "7200.0",
            "Hour-Quota-ResetTime": "1773360871000",
        })
        assert rl.hourly.remaining == 7200

    def test_partial_headers(self):
        rl = RateLimiter()
        rl.update_from_trestle({"Hour-Quota-Limit": "7200.0"})
        assert rl.hourly.limit == 7200
        assert rl.burst.limit == 0


# ── RateLimiter.wait_if_needed ──────────────────────────────────────────────

class TestWaitIfNeeded:
    @patch("mls.rate_limiter.time.sleep")
    @patch("mls.rate_limiter.time.time", return_value=1000.0)
    def test_burst_exhausted_sleeps(self, mock_time, mock_sleep):
        rl = RateLimiter()
        rl.burst.limit = 180
        rl.burst.remaining = 1
        rl.burst.reset_time = 1005.0
        rl.wait_if_needed()
        mock_sleep.assert_called_once_with(5.0)
        assert rl.burst.remaining == 180  # refilled

    @patch("mls.rate_limiter.time.sleep")
    @patch("mls.rate_limiter.time.time", return_value=1000.0)
    def test_hourly_exhausted_sleeps(self, mock_time, mock_sleep):
        rl = RateLimiter()
        rl.hourly.limit = 5000
        rl.hourly.remaining = 1
        rl.hourly.reset_time = 1010.0
        rl.wait_if_needed()
        mock_sleep.assert_called_once_with(10.0)
        assert rl.hourly.remaining == 5000

    @patch("mls.rate_limiter.time.sleep")
    def test_no_sleep_when_quota_available(self, mock_sleep):
        rl = RateLimiter()
        rl.burst.limit = 180
        rl.burst.remaining = 100
        rl.hourly.limit = 5000
        rl.hourly.remaining = 4000
        rl.wait_if_needed()
        mock_sleep.assert_not_called()

    @patch("mls.rate_limiter.time.sleep")
    @patch("mls.rate_limiter.time.time", return_value=1010.0)
    def test_no_sleep_when_reset_already_passed(self, mock_time, mock_sleep):
        rl = RateLimiter()
        rl.burst.limit = 180
        rl.burst.remaining = 1
        rl.burst.reset_time = 1005.0  # already in the past
        rl.wait_if_needed()
        mock_sleep.assert_not_called()

    @patch("mls.rate_limiter.time.sleep")
    def test_no_sleep_when_limit_is_zero(self, mock_sleep):
        rl = RateLimiter()
        rl.burst.remaining = 0  # but limit is 0 = not initialized
        rl.wait_if_needed()
        mock_sleep.assert_not_called()


# ── RateLimiter.decrement ───────────────────────────────────────────────────

class TestDecrement:
    def test_decrements_both(self):
        rl = RateLimiter()
        rl.burst.remaining = 10
        rl.hourly.remaining = 100
        rl.decrement()
        assert rl.burst.remaining == 9
        assert rl.hourly.remaining == 99
        assert rl.total_requests == 1

    def test_doesnt_go_negative(self):
        rl = RateLimiter()
        rl.burst.remaining = 0
        rl.hourly.remaining = 0
        rl.decrement()
        assert rl.burst.remaining == 0
        assert rl.hourly.remaining == 0
        assert rl.total_requests == 1


# ── RateLimiter.backoff_sleep ───────────────────────────────────────────────

class TestBackoffSleep:
    @patch("mls.rate_limiter.random.uniform", return_value=0.25)
    @patch("mls.rate_limiter.time.sleep")
    def test_attempt_0(self, mock_sleep, mock_rand):
        rl = RateLimiter(backoff_base=1.0, backoff_max=60.0)
        rl.backoff_sleep(0)
        # delay = min(1 * 2^0, 60) = 1.0, jitter = 0.25, total = 1.25
        mock_sleep.assert_called_once_with(1.25)

    @patch("mls.rate_limiter.random.uniform", return_value=0.0)
    @patch("mls.rate_limiter.time.sleep")
    def test_capped_at_max(self, mock_sleep, mock_rand):
        rl = RateLimiter(backoff_base=1.0, backoff_max=60.0)
        rl.backoff_sleep(10)  # 2^10 = 1024, capped to 60
        mock_sleep.assert_called_once_with(60.0)


# ── RateLimiter.status ──────────────────────────────────────────────────────

class TestStatus:
    def test_returns_dict(self):
        rl = RateLimiter()
        rl.hourly.limit = 5000
        rl.hourly.remaining = 4900
        rl.burst.limit = 334
        rl.burst.remaining = 320
        rl.total_requests = 5
        s = rl.status()
        assert s == {
            "total_requests": 5,
            "hourly_remaining": 4900,
            "hourly_limit": 5000,
            "burst_remaining": 320,
            "burst_limit": 334,
        }
