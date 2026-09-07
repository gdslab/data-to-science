import asyncio
import logging
from typing import Any, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.utils import titiler as titiler_utils
from app.utils.titiler import (
    parse_titiler_major_version,
    parse_titiler_version,
    verify_titiler_version,
)

TITILER_URL = "http://titiler:8888"
TITILER_LOGGER = "app.utils.titiler"


@pytest.fixture(autouse=True)
def reset_titiler_status() -> Generator[None, None, None]:
    """Clear the cached probe result so tests cannot leak state into each other."""
    titiler_utils.titiler_status.version = None
    titiler_utils.titiler_status.compatible = None
    yield
    titiler_utils.titiler_status.version = None
    titiler_utils.titiler_status.compatible = None


def _mock_healthz_response(version: str, status_code: int = 200) -> MagicMock:
    """Create a mock /healthz response reporting a titiler version."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = {
        "versions": {"titiler": version, "rasterio": "1.5.0"}
    }
    return mock_response


def _mock_titiler_client(
    mock_async_client_cls: MagicMock,
    response: Optional[MagicMock] = None,
    side_effect: Optional[Exception] = None,
) -> AsyncMock:
    """Wire an AsyncMock httpx client onto a patched AsyncClient class."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response, side_effect=side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client
    return mock_client


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"versions": {"titiler": "2.2.1"}}, "2.2.1"),
        ({"versions": {"titiler": "1.2.0"}}, "1.2.0"),
        ({"versions": {}}, None),
        ({}, None),
        ({"versions": "2.2.1"}, None),
        ("2.2.1", None),
        (None, None),
    ],
)
def test_parse_titiler_version(payload: Any, expected: Optional[str]) -> None:
    assert parse_titiler_version(payload) == expected


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"versions": {"titiler": "2.2.1"}}, 2),
        ({"versions": {"titiler": "1.2.0"}}, 1),
        ({"versions": {"titiler": "10.0.0"}}, 10),
        ({"versions": {"titiler": "dev"}}, None),
        ({"versions": {}}, None),
        ({}, None),
        (None, None),
    ],
)
def test_parse_titiler_major_version(payload: Any, expected: Optional[int]) -> None:
    assert parse_titiler_major_version(payload) == expected


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_accepts_supported_version(
    mock_async_client_cls: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_client = _mock_titiler_client(
        mock_async_client_cls, response=_mock_healthz_response("2.2.1")
    )

    with caplog.at_level(logging.INFO, logger=TITILER_LOGGER):
        result = asyncio.run(verify_titiler_version(TITILER_URL, delay=0))

    assert result.version == "2.2.1"
    assert result.compatible is True
    assert mock_client.get.call_args.args[0] == f"{TITILER_URL}/healthz"
    assert "TiTiler 2.2.1 detected" in caplog.text


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_rejects_unsupported_version(
    mock_async_client_cls: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_titiler_client(
        mock_async_client_cls, response=_mock_healthz_response("1.2.0")
    )

    with caplog.at_level(logging.INFO, logger=TITILER_LOGGER):
        result = asyncio.run(verify_titiler_version(TITILER_URL, delay=0))

    assert result.version == "1.2.0"
    assert result.compatible is False
    errors = [record for record in caplog.records if record.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "requires TiTiler 2.0 or later" in errors[0].message


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_handles_unreadable_payload(
    mock_async_client_cls: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"detail": "unexpected"}
    mock_client = _mock_titiler_client(mock_async_client_cls, response=mock_response)

    with caplog.at_level(logging.INFO, logger=TITILER_LOGGER):
        result = asyncio.run(verify_titiler_version(TITILER_URL, delay=0))

    assert result.version is None
    assert result.compatible is None
    # A response that parsed but was not understood is not retried.
    assert mock_client.get.await_count == 1


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_retries_then_gives_up_when_unreachable(
    mock_async_client_cls: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_client = _mock_titiler_client(
        mock_async_client_cls, side_effect=httpx.ConnectError("connection refused")
    )

    with caplog.at_level(logging.INFO, logger=TITILER_LOGGER):
        result = asyncio.run(verify_titiler_version(TITILER_URL, attempts=3, delay=0))

    assert result.version is None
    assert result.compatible is None
    assert mock_client.get.await_count == 3
    warnings = [
        record for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    assert "Could not verify TiTiler version" in warnings[0].message


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_retries_on_non_200(
    mock_async_client_cls: MagicMock,
) -> None:
    mock_client = _mock_titiler_client(
        mock_async_client_cls, response=_mock_healthz_response("2.2.1", status_code=503)
    )

    result = asyncio.run(verify_titiler_version(TITILER_URL, attempts=2, delay=0))

    assert result.compatible is None
    assert mock_client.get.await_count == 2


@patch("app.utils.titiler.httpx.AsyncClient")
def test_verify_titiler_version_trims_trailing_slash(
    mock_async_client_cls: MagicMock,
) -> None:
    mock_client = _mock_titiler_client(
        mock_async_client_cls, response=_mock_healthz_response("2.2.1")
    )

    asyncio.run(verify_titiler_version(f"{TITILER_URL}/", delay=0))

    assert mock_client.get.call_args.args[0] == f"{TITILER_URL}/healthz"
