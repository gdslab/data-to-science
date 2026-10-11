from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import configure_cors


def _client(allowed_origins: str) -> TestClient:
    """Build an isolated app with CORS configured from the given allowlist."""
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    configure_cors(app, allowed_origins)
    return TestClient(app)


def _preflight(client: TestClient, origin: str) -> "object":
    return client.options(
        "/ping",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )


def test_allowed_origin_gets_credentialed_cors() -> None:
    client = _client("https://geolibre.app,tauri://localhost")

    resp = _preflight(client, "https://geolibre.app")

    assert resp.headers.get("access-control-allow-origin") == "https://geolibre.app"
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in resp.headers.get("access-control-allow-methods", "")


def test_non_http_origin_is_allowed() -> None:
    """Origins such as tauri://localhost (non-HTTP scheme) must be honored."""
    client = _client("https://geolibre.app,tauri://localhost")

    resp = _preflight(client, "tauri://localhost")

    assert resp.headers.get("access-control-allow-origin") == "tauri://localhost"


def test_disallowed_origin_is_not_reflected() -> None:
    client = _client("https://geolibre.app")

    resp = _preflight(client, "https://evil.example")

    # The browser blocks the request because the origin is never echoed back.
    assert resp.headers.get("access-control-allow-origin") is None


def test_empty_allowlist_falls_back_to_anonymous_get() -> None:
    client = _client("")

    resp = client.get("/ping", headers={"Origin": "https://anything.example"})

    assert resp.headers.get("access-control-allow-origin") == "*"
    assert resp.headers.get("access-control-allow-credentials") is None


def test_whitespace_and_blank_entries_are_ignored() -> None:
    client = _client("  ,  https://geolibre.app  , ")

    resp = _preflight(client, "https://geolibre.app")

    assert resp.headers.get("access-control-allow-origin") == "https://geolibre.app"
