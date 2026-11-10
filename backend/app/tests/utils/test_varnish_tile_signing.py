"""Vector tile requests sent to the running varnish service.

These exercise the checks in varnish/default.vcl itself, so they are skipped
where the varnish service is not on the network.
"""

from urllib.parse import urlsplit

import httpx

from app.api.utils import get_tile_url_with_signed_payload
from app.core.config import settings
from app.tests.conftest import pytest_requires_varnish

VARNISH_BASE_URL = "http://varnish"
LAYER_ID = "57WI-EOF_P4"


def signed_tile_request() -> tuple[str, dict[str, str]]:
    """Build a signed tile request as varnish receives it.

    Returns:
        tuple[str, dict[str, str]]: Tile path and the still-encoded query values.
    """
    tile_url = urlsplit(
        get_tile_url_with_signed_payload(LAYER_ID).removeprefix(settings.API_DOMAIN)
    )
    # nginx strips the /mvt prefix before the request reaches varnish
    path = tile_url.path.removeprefix("/mvt").format(z=0, x=0, y=0)
    values = dict(pair.split("=", 1) for pair in tile_url.query.split("&"))
    return path, values


def get_tile(path: str, values: dict[str, str], prefix: str = "") -> httpx.Response:
    """Request a tile from varnish with the query values sent as given.

    Args:
        path (str): Tile path.
        values (dict[str, str]): Still-encoded query values.
        prefix (str): Raw query text placed ahead of the values, for names a
            dict cannot repeat.
    """
    query = prefix + "&".join(f"{name}={value}" for name, value in values.items())
    return httpx.get(f"{VARNISH_BASE_URL}{path}?{query}", timeout=10)


@pytest_requires_varnish
def test_varnish_accepts_signed_tile_url() -> None:
    """Varnish lets through the tile URL the backend signs."""
    path, values = signed_tile_request()

    response = get_tile(path, values)

    assert response.status_code not in (400, 403)


@pytest_requires_varnish
def test_varnish_rejects_signed_query_on_another_path() -> None:
    """A valid signature cannot be replayed against a different table."""
    _, values = signed_tile_request()

    response = get_tile("/public.other_table/0/0/0.pbf", values)

    assert response.status_code == 403
    assert response.reason_phrase == "Invalid tile path"


@pytest_requires_varnish
def test_varnish_rejects_bytes_moved_between_filter_and_limit() -> None:
    """Moving a byte from limit into filter keeps the payload but is rejected."""
    path, values = signed_tile_request()
    assert values["limit"] == "-1"
    # expires + filter + limit is unchanged, so the signature still matches
    values["filter"] += "-"
    values["limit"] = "1"

    response = get_tile(path, values)

    assert response.status_code == 400
    assert response.reason_phrase == "Invalid parameters"


@pytest_requires_varnish
def test_varnish_drops_unverified_query_params() -> None:
    """A filter under an encoded name does not reach the tile server."""
    path, values = signed_tile_request()
    expected = get_tile(path, values)
    assert expected.is_success

    # pg_tileserv decodes the name and would read this invalid filter first
    response = get_tile(path, {"fil%74er": "%28", **values})

    assert response.status_code == expected.status_code


@pytest_requires_varnish
def test_varnish_ignores_repeated_filter() -> None:
    """An unsigned filter placed ahead of the signed one is not executed."""
    path, values = signed_tile_request()
    expected = get_tile(path, values)
    assert expected.is_success

    # pg_tileserv reads the first filter; this one is invalid, so it would fail
    response = get_tile(path, values, prefix="filter=%28&limit=-1&")

    assert response.status_code == expected.status_code


@pytest_requires_varnish
def test_varnish_rejects_tampered_filter() -> None:
    """A filter for another layer does not match the original signature."""
    path, values = signed_tile_request()
    values["filter"] = values["filter"].replace(LAYER_ID, "anotherLayer")

    response = get_tile(path, values)

    assert response.status_code == 403
    assert response.reason_phrase == "Invalid signature"
