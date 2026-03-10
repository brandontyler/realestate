"""Provider-agnostic MLS client for RESO Web API (OData 4.0).

Supports:
  - Bridge Interactive (static server token as query param)
  - Trestle / CoreLogic (OAuth2 client_credentials → Bearer header)

Auth, URL construction, and rate limiting are abstracted per provider.
OData query syntax ($filter, $select, $top, $expand, $orderby, $count, $skip)
is identical across providers.
"""

import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# HTTP status codes that are safe to retry
_RETRYABLE_STATUS = {429, 504}

# Default request timeout (connect, read) in seconds
_DEFAULT_TIMEOUT = (10, 30)


class MLSClient(ABC):
    """Base class — handles OData queries, pagination, rate limiting, retries."""

    def __init__(self):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()

    # -- Subclass hooks --

    @abstractmethod
    def _build_url(self, resource: str) -> str:
        """Return the full base URL for a resource (e.g. Property)."""

    @abstractmethod
    def _apply_auth(self, params: dict, headers: dict) -> None:
        """Mutate params/headers to add authentication."""

    @abstractmethod
    def _update_rate_limits(self, resp: requests.Response) -> None:
        """Read provider-specific rate-limit headers."""

    @abstractmethod
    def _nextlink_needs_auth(self) -> bool:
        """Whether @odata.nextLink URLs need auth re-applied."""

    # -- Public API --

    def query(
        self,
        resource: str,
        *,
        filter: str | None = None,
        select: list[str] | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        count: bool = False,
    ) -> dict[str, Any]:
        """Execute an OData query and return the JSON response."""
        url = self._build_url(resource)
        params: dict[str, str] = {}

        if filter:
            params["$filter"] = filter
        if select:
            params["$select"] = ",".join(select)
        if expand:
            params["$expand"] = expand
        if orderby:
            params["$orderby"] = orderby
        if top is not None:
            params["$top"] = str(top)
        if skip is not None:
            params["$skip"] = str(skip)
        if count:
            params["$count"] = "true"

        return self._execute(url, params)

    def get_by_key(
        self,
        resource: str,
        key: str,
        *,
        select: list[str] | None = None,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Fetch a single entity by its key."""
        url = f"{self._build_url(resource)}('{key}')"
        params: dict[str, str] = {}
        if select:
            params["$select"] = ",".join(select)
        if expand:
            params["$expand"] = expand
        return self._execute(url, params)

    def fetch_next(self, next_link: str) -> dict[str, Any]:
        """Follow an @odata.nextLink for pagination."""
        if self._nextlink_needs_auth():
            # Trestle nextLinks don't include auth — we need to add it
            headers: dict[str, str] = {"Accept": "application/json"}
            self._apply_auth({}, headers)  # only need headers for Trestle
            return self._execute_raw(next_link, headers)
        return self._execute_raw(next_link, {"Accept": "application/json"})

    def get_metadata(self) -> str:
        """Fetch OData $metadata (XML). Returns raw text."""
        url = self._build_url("$metadata")
        headers: dict[str, str] = {"Accept": "application/xml"}
        params: dict[str, str] = {}
        self._apply_auth(params, headers)
        full_url = _build_odata_url(url, params)

        self.rate_limiter.wait_if_needed()
        logger.info("MLS metadata request: %s", _safe_log_url(full_url))
        resp = self.session.get(full_url, headers=headers, timeout=_DEFAULT_TIMEOUT)
        self._update_rate_limits(resp)
        self.rate_limiter.decrement()
        resp.raise_for_status()
        return resp.text

    # -- Internal --

    def _execute(self, url: str, params: dict) -> dict[str, Any]:
        headers: dict[str, str] = {"Accept": "application/json"}
        self._apply_auth(params, headers)
        full_url = _build_odata_url(url, params)
        return self._execute_raw(full_url, headers)

    def _execute_raw(self, full_url: str, headers: dict) -> dict[str, Any]:
        for attempt in range(self.rate_limiter.max_retries + 1):
            self.rate_limiter.wait_if_needed()

            logger.info(
                "MLS request [#%d]: %s",
                self.rate_limiter.total_requests + 1,
                _safe_log_url(full_url),
            )
            resp = self.session.get(full_url, headers=headers, timeout=_DEFAULT_TIMEOUT)

            self._update_rate_limits(resp)

            logger.info(
                "MLS response: %d | quota: hourly=%d/%d burst=%d/%d",
                resp.status_code,
                self.rate_limiter.hourly.remaining,
                self.rate_limiter.hourly.limit,
                self.rate_limiter.burst.remaining,
                self.rate_limiter.burst.limit,
            )

            if resp.status_code == 200:
                self.rate_limiter.decrement()
                return resp.json()

            if resp.status_code in _RETRYABLE_STATUS:
                # Don't decrement on retryable errors — the server rejected
                # the request, so it shouldn't count against our local quota.
                if attempt < self.rate_limiter.max_retries:
                    self.rate_limiter.backoff_sleep(attempt)
                    continue
                logger.error(
                    "%d after %d retries, giving up. URL: %s",
                    resp.status_code,
                    self.rate_limiter.max_retries,
                    _safe_log_url(full_url),
                )

            # Non-retryable error — log body for debugging
            logger.error(
                "MLS error %d: %s", resp.status_code, resp.text[:500]
            )
            resp.raise_for_status()

        return {}  # pragma: no cover — unreachable, satisfies type checker


class BridgeClient(MLSClient):
    """Bridge Interactive — static server token as `access_token` query param.

    Env vars:
        BRIDGE_API_URL    - e.g. https://api.bridgedataoutput.com/api/v2
        BRIDGE_API_TOKEN  - server token from dashboard
        BRIDGE_DATASET    - e.g. actris_ref
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        dataset: str | None = None,
    ):
        super().__init__()
        self.base_url = (base_url or os.environ["BRIDGE_API_URL"]).rstrip("/")
        self.token = token or os.environ["BRIDGE_API_TOKEN"]
        self.dataset = dataset or os.environ.get("BRIDGE_DATASET", "actris_ref")

    def _build_url(self, resource: str) -> str:
        return f"{self.base_url}/OData/{self.dataset}/{resource}"

    def _apply_auth(self, params: dict, headers: dict) -> None:
        params["access_token"] = self.token

    def _update_rate_limits(self, resp: requests.Response) -> None:
        self.rate_limiter.update_from_bridge(resp.headers)

    def _nextlink_needs_auth(self) -> bool:
        # Bridge embeds access_token in nextLink URLs
        return False


class TrestleClient(MLSClient):
    """Trestle / CoreLogic — OAuth2 client_credentials → Bearer header.

    Env vars:
        TRESTLE_API_URL       - e.g. https://api.cotality.com/trestle
        TRESTLE_CLIENT_ID
        TRESTLE_CLIENT_SECRET
    """

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        super().__init__()
        self.base_url = (base_url or os.environ["TRESTLE_API_URL"]).rstrip("/")
        self.client_id = client_id or os.environ["TRESTLE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["TRESTLE_CLIENT_SECRET"]
        self._token: str | None = None
        self._token_expires: float = 0.0

    def _ensure_token(self) -> str:
        """Get or refresh the OAuth2 token. Tokens are valid for 8 hours."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        token_url = f"{self.base_url}/oidc/connect/token"
        logger.info("Trestle: requesting new OAuth2 token")
        resp = self.session.post(
            token_url,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "api",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=_DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 28800)
        logger.info("Trestle token refreshed, expires in %ds", data.get("expires_in", 28800))
        return self._token

    def _build_url(self, resource: str) -> str:
        return f"{self.base_url}/odata/{resource}"

    def _apply_auth(self, params: dict, headers: dict) -> None:
        headers["Authorization"] = f"Bearer {self._ensure_token()}"

    def _update_rate_limits(self, resp: requests.Response) -> None:
        self.rate_limiter.update_from_trestle(resp.headers)

    def _nextlink_needs_auth(self) -> bool:
        # Trestle nextLinks don't include auth
        return True


def create_client(provider: str | None = None) -> MLSClient:
    """Factory — create the right client based on env var or explicit provider.

    Args:
        provider: "bridge" or "trestle". If None, reads MLS_PROVIDER env var.
    """
    provider = (provider or os.environ.get("MLS_PROVIDER", "bridge")).lower()
    if provider == "bridge":
        return BridgeClient()
    elif provider == "trestle":
        return TrestleClient()
    else:
        raise ValueError(f"Unknown MLS provider: {provider}")


def _build_odata_url(base_url: str, params: dict) -> str:
    """Build URL preserving OData $ params without percent-encoding the $.

    requests.utils.quote encodes $ as %24 which Bridge rejects.
    We keep $, single quotes, parens, semicolons, and # literal since
    OData filter/expand syntax uses them.
    """
    if not params:
        return base_url
    parts = []
    for k, v in params.items():
        encoded_val = requests.utils.quote(str(v), safe="()',;$=*# ")
        parts.append(f"{k}={encoded_val}")
    return f"{base_url}?{'&'.join(parts)}"


def _safe_log_url(url: str) -> str:
    """Redact access_token from URLs before logging."""
    return re.sub(r"access_token=[^&]+", "access_token=***", url)
