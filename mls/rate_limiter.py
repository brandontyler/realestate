"""Rate limiter that reads live quota headers from Bridge and Trestle APIs.

Bridge headers:
    application-ratelimit-limit / remaining / reset  (hourly)
    burst-ratelimit-limit / remaining / reset         (per-minute)

Trestle headers:
    Hour-Quota-Limit / Minute-Quota-Limit / Hour-Quota-ResetTime

On 429 or 504: exponential backoff with jitter (1s → 2s → 4s … max 60s, 3 retries).
"""

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class QuotaBucket:
    limit: int = 0
    remaining: int = 0
    reset_time: float = 0.0  # unix timestamp


@dataclass
class RateLimiter:
    hourly: QuotaBucket = field(default_factory=QuotaBucket)
    burst: QuotaBucket = field(default_factory=QuotaBucket)
    total_requests: int = 0

    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 60.0

    def update_from_bridge(self, headers: dict) -> None:
        """Parse Bridge rate-limit headers. Bridge returns remaining directly."""
        if "application-ratelimit-limit" in headers:
            self.hourly.limit = int(headers["application-ratelimit-limit"])
        if "application-ratelimit-remaining" in headers:
            self.hourly.remaining = int(headers["application-ratelimit-remaining"])
        if "application-ratelimit-reset" in headers:
            self.hourly.reset_time = _parse_iso(headers["application-ratelimit-reset"])

        if "burst-ratelimit-limit" in headers:
            self.burst.limit = int(headers["burst-ratelimit-limit"])
        if "burst-ratelimit-remaining" in headers:
            self.burst.remaining = int(headers["burst-ratelimit-remaining"])
        if "burst-ratelimit-reset" in headers:
            self.burst.reset_time = _parse_iso(headers["burst-ratelimit-reset"])

    def update_from_trestle(self, headers: dict) -> None:
        """Parse Trestle rate-limit headers.

        Trestle only returns limit + reset, not remaining.
        We track remaining ourselves via decrement().
        On first call, seed remaining from limit. After that, only
        update limit/reset — don't reset remaining.
        """
        if "Hour-Quota-Limit" in headers:
            new_limit = int(float(headers["Hour-Quota-Limit"]))
            if self.hourly.limit == 0:
                # First response — seed remaining
                self.hourly.remaining = new_limit
            self.hourly.limit = new_limit
        if "Minute-Quota-Limit" in headers:
            new_limit = int(float(headers["Minute-Quota-Limit"]))
            if self.burst.limit == 0:
                self.burst.remaining = new_limit
            self.burst.limit = new_limit
        if "Hour-Quota-ResetTime" in headers:
            new_reset = int(headers["Hour-Quota-ResetTime"]) / 1000.0
            # If reset time changed, the quota window rolled over — refill
            if new_reset != self.hourly.reset_time and self.hourly.reset_time > 0:
                self.hourly.remaining = self.hourly.limit
            self.hourly.reset_time = new_reset

    def wait_if_needed(self) -> None:
        """Sleep if we're close to hitting either quota."""
        now = time.time()

        # Check burst (per-minute) first — tighter window
        if self.burst.limit > 0 and self.burst.remaining <= 1:
            wait = max(0, self.burst.reset_time - now)
            if wait > 0:
                logger.warning(
                    "Burst quota exhausted (%d/%d), sleeping %.1fs until reset",
                    self.burst.remaining, self.burst.limit, wait,
                )
                time.sleep(wait)
                # After sleeping past reset, refill burst
                self.burst.remaining = self.burst.limit

        # Check hourly quota
        if self.hourly.limit > 0 and self.hourly.remaining <= 1:
            wait = max(0, self.hourly.reset_time - now)
            if wait > 0:
                logger.warning(
                    "Hourly quota exhausted (%d/%d), sleeping %.1fs until reset",
                    self.hourly.remaining, self.hourly.limit, wait,
                )
                time.sleep(wait)
                self.hourly.remaining = self.hourly.limit

    def decrement(self) -> None:
        """Track consumption after a successful request."""
        self.total_requests += 1
        if self.burst.remaining > 0:
            self.burst.remaining -= 1
        if self.hourly.remaining > 0:
            self.hourly.remaining -= 1

    def backoff_sleep(self, attempt: int) -> None:
        """Exponential backoff with jitter."""
        delay = min(self.backoff_base * (2 ** attempt), self.backoff_max)
        jitter = random.uniform(0, delay * 0.5)
        total = delay + jitter
        logger.warning("Retryable error, backoff attempt %d: sleeping %.1fs", attempt + 1, total)
        time.sleep(total)

    def status(self) -> dict:
        """Return current quota status for logging/debugging."""
        return {
            "total_requests": self.total_requests,
            "hourly_remaining": self.hourly.remaining,
            "hourly_limit": self.hourly.limit,
            "burst_remaining": self.burst.remaining,
            "burst_limit": self.burst.limit,
        }


def _parse_iso(val: str) -> float:
    """Parse ISO 8601 timestamp to unix time."""
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0
