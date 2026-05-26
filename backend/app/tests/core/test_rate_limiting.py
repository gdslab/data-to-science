from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.limiter import _key_func


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture()
def rate_limited_client():
    """Isolated FastAPI app with rate limiting enabled."""
    test_limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
    app = FastAPI()
    app.state.limiter = test_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/limited")
    @test_limiter.limit("3/minute")
    def limited_endpoint(request: Request):
        return {"ok": True}

    @app.get("/unlimited")
    def unlimited_endpoint(request: Request):
        return {"ok": True}

    return TestClient(app)


# -- Rate limit enforcement ----------------------------------------------------


def test_rate_limit_returns_429(rate_limited_client: TestClient) -> None:
    for _ in range(3):
        resp = rate_limited_client.get("/limited")
        assert resp.status_code == 200

    resp = rate_limited_client.get("/limited")
    assert resp.status_code == 429


def test_unlimited_endpoint_not_affected(rate_limited_client: TestClient) -> None:
    for _ in range(20):
        resp = rate_limited_client.get("/unlimited")
        assert resp.status_code == 200


# -- Key function unit tests ---------------------------------------------------


def _make_mock_request(headers=None, client_host="10.0.0.1"):
    request = MagicMock(spec=Request)
    request.headers = headers or {}
    request.client = MagicMock()
    request.client.host = client_host
    return request


def test_key_func_prefers_x_real_ip() -> None:
    request = _make_mock_request(
        headers={
            "X-Real-IP": "1.2.3.4",
            "CF-Connecting-IP": "5.6.7.8",
            "X-Forwarded-For": "9.10.11.12",
        }
    )
    assert _key_func(request) == "1.2.3.4"


def test_key_func_falls_back_to_cf_connecting_ip() -> None:
    request = _make_mock_request(headers={"CF-Connecting-IP": "5.6.7.8"})
    assert _key_func(request) == "5.6.7.8"


def test_key_func_falls_back_to_x_forwarded_for_first_entry() -> None:
    request = _make_mock_request(
        headers={"X-Forwarded-For": "9.10.11.12, 172.16.0.1"}
    )
    assert _key_func(request) == "9.10.11.12"


def test_key_func_falls_back_to_client_host() -> None:
    request = _make_mock_request(client_host="192.168.1.1")
    assert _key_func(request) == "192.168.1.1"


def test_key_func_returns_unknown_when_no_client() -> None:
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = None
    assert _key_func(request) == "unknown"
