"""Unit tests for mls/client.py — 100% coverage target.

All HTTP calls are mocked via `responses`. No live API calls.
"""

import os
import time
from unittest.mock import patch, MagicMock

import pytest
import responses

from mls.client import (
    BridgeClient,
    TrestleClient,
    MLSClient,
    create_client,
    _build_odata_url,
    _safe_log_url,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

BRIDGE_BASE = "https://api.bridgedataoutput.com/api/v2"
BRIDGE_TOKEN = "test_server_token_abc123"
BRIDGE_DATASET = "actris_ref"

TRESTLE_BASE = "https://api.cotality.com/trestle"
TRESTLE_CLIENT_ID = "test_client_id"
TRESTLE_CLIENT_SECRET = "test_client_secret"

BRIDGE_RATE_HEADERS = {
    "application-ratelimit-limit": "5000",
    "application-ratelimit-remaining": "4999",
    "application-ratelimit-reset": "2026-03-10T21:00:00Z",
    "burst-ratelimit-limit": "334",
    "burst-ratelimit-remaining": "333",
    "burst-ratelimit-reset": "2026-03-10T20:15:00Z",
}

TRESTLE_RATE_HEADERS = {
    "Hour-Quota-Limit": "7200.0",
    "Minute-Quota-Limit": "180.0",
    "Hour-Quota-ResetTime": "1773357271000",
}

SAMPLE_PROPERTY = {
    "ListingKey": "abc123",
    "UnparsedAddress": "123 Main St, Austin TX 78701",
    "ListPrice": 500000,
}

SAMPLE_ODATA_RESPONSE = {
    "@odata.context": "https://example.com/$metadata#Property",
    "@odata.count": 1,
    "value": [SAMPLE_PROPERTY],
}


def make_bridge_client():
    return BridgeClient(
        base_url=BRIDGE_BASE, token=BRIDGE_TOKEN, dataset=BRIDGE_DATASET
    )


def make_trestle_client():
    return TrestleClient(
        base_url=TRESTLE_BASE,
        client_id=TRESTLE_CLIENT_ID,
        client_secret=TRESTLE_CLIENT_SECRET,
    )


# ── _build_odata_url ───────────────────────────────────────────────────────

class TestBuildOdataUrl:
    def test_no_params(self):
        assert _build_odata_url("https://example.com/Property", {}) == "https://example.com/Property"

    def test_preserves_dollar_signs(self):
        url = _build_odata_url("https://example.com/Property", {
            "$filter": "City eq 'Austin'",
            "$top": "10",
        })
        assert "$filter=" in url
        assert "$top=10" in url
        assert "%24" not in url

    def test_preserves_odata_special_chars(self):
        url = _build_odata_url("https://example.com/Property", {
            "$expand": "Media($select=MediaURL;$top=1)",
        })
        assert "($select=MediaURL;$top=1)" in url

    def test_preserves_single_quotes(self):
        url = _build_odata_url("https://example.com/Property", {
            "$filter": "StandardStatus eq 'Closed'",
        })
        assert "'Closed'" in url

    def test_preserves_hash_in_address(self):
        url = _build_odata_url("https://example.com/Property", {
            "$filter": "UnparsedAddress eq '123 Main # 5'",
        })
        assert "# 5" in url


# ── _safe_log_url ──────────────────────────────────────────────────────────

class TestSafeLogUrl:
    def test_redacts_access_token(self):
        url = "https://example.com/Property?$top=1&access_token=secret123&$filter=x"
        safe = _safe_log_url(url)
        assert "secret123" not in safe
        assert "access_token=***" in safe

    def test_no_token_unchanged(self):
        url = "https://example.com/Property?$top=1"
        assert _safe_log_url(url) == url


# ── BridgeClient ────────────────────────────────────────────────────────────

class TestBridgeClient:
    def test_build_url(self):
        c = make_bridge_client()
        assert c._build_url("Property") == f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property"

    def test_apply_auth_adds_query_param(self):
        c = make_bridge_client()
        params, headers = {}, {}
        c._apply_auth(params, headers)
        assert params["access_token"] == BRIDGE_TOKEN
        assert "Authorization" not in headers

    def test_nextlink_needs_auth_false(self):
        c = make_bridge_client()
        assert c._nextlink_needs_auth() is False

    @responses.activate
    def test_query_basic(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        result = c.query("Property", select=["ListingKey"], top=1, count=True)
        assert result["value"][0]["ListingKey"] == "abc123"
        assert c.rate_limiter.hourly.limit == 5000

    @responses.activate
    def test_query_all_params(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        result = c.query(
            "Property",
            filter="City eq 'Austin'",
            select=["ListingKey", "City"],
            expand="Media",
            orderby="ListPrice desc",
            top=10,
            skip=5,
            count=True,
        )
        assert result["value"][0]["ListingKey"] == "abc123"
        req = responses.calls[0].request
        assert "$filter=" in req.url
        assert "$select=" in req.url
        assert "$expand=" in req.url
        assert "$orderby=" in req.url
        assert "$top=10" in req.url
        assert "$skip=5" in req.url
        assert "$count=true" in req.url

    @responses.activate
    def test_get_by_key(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property('abc123')",
            json=SAMPLE_PROPERTY,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        result = c.get_by_key("Property", "abc123")
        assert result["ListingKey"] == "abc123"

    @responses.activate
    def test_get_by_key_with_select_and_expand(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property('abc123')",
            json=SAMPLE_PROPERTY,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        result = c.get_by_key("Property", "abc123", select=["ListingKey"], expand="Media")
        assert result["ListingKey"] == "abc123"
        req = responses.calls[0].request
        assert "$select=ListingKey" in req.url
        assert "$expand=Media" in req.url

    @responses.activate
    def test_fetch_next_no_auth_needed(self):
        next_url = f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property?$top=1&access_token={BRIDGE_TOKEN}&$next=cursor123"
        responses.add(
            responses.GET,
            next_url,
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        result = c.fetch_next(next_url)
        assert result["value"][0]["ListingKey"] == "abc123"

    @responses.activate
    def test_get_metadata(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/$metadata",
            body='<edmx:Edmx Version="4.0"><EntityType Name="Property"/></edmx:Edmx>',
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        meta = c.get_metadata()
        assert "EntityType" in meta

    @responses.activate
    def test_retry_on_429(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json={"error": "rate limited"},
            status=429,
            headers=BRIDGE_RATE_HEADERS,
        )
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        c.rate_limiter.backoff_base = 0.001  # fast for tests
        result = c.query("Property", top=1)
        assert result["value"][0]["ListingKey"] == "abc123"
        assert len(responses.calls) == 2

    @responses.activate
    def test_retry_on_504(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            body="Gateway Timeout",
            status=504,
            headers=BRIDGE_RATE_HEADERS,
        )
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        c.rate_limiter.backoff_base = 0.001
        result = c.query("Property", top=1)
        assert len(responses.calls) == 2

    @responses.activate
    def test_429_exhausts_retries(self):
        for _ in range(4):  # 1 initial + 3 retries
            responses.add(
                responses.GET,
                f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
                json={"error": "rate limited"},
                status=429,
                headers=BRIDGE_RATE_HEADERS,
            )
        c = make_bridge_client()
        c.rate_limiter.backoff_base = 0.001
        with pytest.raises(Exception):
            c.query("Property", top=1)
        assert len(responses.calls) == 4

    @responses.activate
    def test_400_no_retry(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json={"error": {"code": 400, "message": "Bad Request"}},
            status=400,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        with pytest.raises(Exception):
            c.query("Property", filter="bad filter")
        assert len(responses.calls) == 1  # no retry

    @responses.activate
    def test_rate_limits_tracked(self):
        responses.add(
            responses.GET,
            f"{BRIDGE_BASE}/OData/{BRIDGE_DATASET}/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=BRIDGE_RATE_HEADERS,
        )
        c = make_bridge_client()
        c.query("Property", top=1)
        assert c.rate_limiter.hourly.limit == 5000
        assert c.rate_limiter.burst.limit == 334
        assert c.rate_limiter.total_requests == 1

    def test_init_from_env(self):
        env = {
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
            "BRIDGE_DATASET": BRIDGE_DATASET,
        }
        with patch.dict(os.environ, env):
            c = BridgeClient()
            assert c.base_url == BRIDGE_BASE
            assert c.token == BRIDGE_TOKEN
            assert c.dataset == BRIDGE_DATASET

    def test_init_default_dataset(self):
        env = {
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
        }
        with patch.dict(os.environ, env, clear=False):
            # Remove BRIDGE_DATASET if present
            os.environ.pop("BRIDGE_DATASET", None)
            c = BridgeClient()
            assert c.dataset == "actris_ref"


# ── TrestleClient ──────────────────────────────────────────────────────────

class TestTrestleClient:
    def test_build_url(self):
        c = make_trestle_client()
        assert c._build_url("Property") == f"{TRESTLE_BASE}/odata/Property"

    def test_nextlink_needs_auth_true(self):
        c = make_trestle_client()
        assert c._nextlink_needs_auth() is True

    @responses.activate
    def test_oauth_token_fetch(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800, "token_type": "Bearer"},
            status=200,
        )
        c = make_trestle_client()
        token = c._ensure_token()
        assert token == "jwt_token_here"
        assert c._token_expires > time.time()

    @responses.activate
    def test_token_cached(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800, "token_type": "Bearer"},
            status=200,
        )
        c = make_trestle_client()
        c._ensure_token()
        c._ensure_token()  # should not make another POST
        assert len(responses.calls) == 1

    @responses.activate
    def test_token_refreshed_when_expired(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "token1", "expires_in": 28800},
            status=200,
        )
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "token2", "expires_in": 28800},
            status=200,
        )
        c = make_trestle_client()
        c._ensure_token()
        # Force expiry
        c._token_expires = time.time() - 1
        token = c._ensure_token()
        assert token == "token2"
        assert len(responses.calls) == 2

    @responses.activate
    def test_apply_auth_adds_bearer_header(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800},
            status=200,
        )
        c = make_trestle_client()
        params, headers = {}, {}
        c._apply_auth(params, headers)
        assert headers["Authorization"] == "Bearer jwt_token_here"
        assert "access_token" not in params

    @responses.activate
    def test_query(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{TRESTLE_BASE}/odata/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=TRESTLE_RATE_HEADERS,
        )
        c = make_trestle_client()
        result = c.query("Property", top=1)
        assert result["value"][0]["ListingKey"] == "abc123"
        # Verify Bearer header was sent
        get_req = responses.calls[1].request
        assert get_req.headers["Authorization"] == "Bearer jwt_token_here"

    @responses.activate
    def test_fetch_next_applies_auth(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800},
            status=200,
        )
        next_url = f"{TRESTLE_BASE}/odata/Property?$top=1000&$skip=1000"
        responses.add(
            responses.GET,
            next_url,
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=TRESTLE_RATE_HEADERS,
        )
        c = make_trestle_client()
        result = c.fetch_next(next_url)
        get_req = responses.calls[1].request
        assert "Bearer" in get_req.headers.get("Authorization", "")

    @responses.activate
    def test_trestle_rate_limits_tracked(self):
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here", "expires_in": 28800},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{TRESTLE_BASE}/odata/Property",
            json=SAMPLE_ODATA_RESPONSE,
            status=200,
            headers=TRESTLE_RATE_HEADERS,
        )
        c = make_trestle_client()
        c.query("Property", top=1)
        assert c.rate_limiter.hourly.limit == 7200
        assert c.rate_limiter.burst.limit == 180

    def test_init_from_env(self):
        env = {
            "TRESTLE_API_URL": TRESTLE_BASE,
            "TRESTLE_CLIENT_ID": TRESTLE_CLIENT_ID,
            "TRESTLE_CLIENT_SECRET": TRESTLE_CLIENT_SECRET,
        }
        with patch.dict(os.environ, env):
            c = TrestleClient()
            assert c.base_url == TRESTLE_BASE
            assert c.client_id == TRESTLE_CLIENT_ID

    @responses.activate
    def test_token_default_expires_in(self):
        """Token response without expires_in defaults to 28800."""
        responses.add(
            responses.POST,
            f"{TRESTLE_BASE}/oidc/connect/token",
            json={"access_token": "jwt_token_here"},
            status=200,
        )
        c = make_trestle_client()
        c._ensure_token()
        assert c._token_expires > time.time() + 28000


# ── create_client factory ──────────────────────────────────────────────────

class TestCreateClient:
    def test_bridge_explicit(self):
        env = {
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
        }
        with patch.dict(os.environ, env):
            c = create_client("bridge")
            assert isinstance(c, BridgeClient)

    def test_trestle_explicit(self):
        env = {
            "TRESTLE_API_URL": TRESTLE_BASE,
            "TRESTLE_CLIENT_ID": TRESTLE_CLIENT_ID,
            "TRESTLE_CLIENT_SECRET": TRESTLE_CLIENT_SECRET,
        }
        with patch.dict(os.environ, env):
            c = create_client("trestle")
            assert isinstance(c, TrestleClient)

    def test_from_env_var(self):
        env = {
            "MLS_PROVIDER": "bridge",
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
        }
        with patch.dict(os.environ, env):
            c = create_client()
            assert isinstance(c, BridgeClient)

    def test_default_is_bridge(self):
        env = {
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("MLS_PROVIDER", None)
            c = create_client()
            assert isinstance(c, BridgeClient)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown MLS provider"):
            create_client("zillow")

    def test_case_insensitive(self):
        env = {
            "BRIDGE_API_URL": BRIDGE_BASE,
            "BRIDGE_API_TOKEN": BRIDGE_TOKEN,
        }
        with patch.dict(os.environ, env):
            c = create_client("BRIDGE")
            assert isinstance(c, BridgeClient)
