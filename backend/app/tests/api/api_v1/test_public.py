from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_approved_user, get_current_user
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like

# Center of test.tif (EPSG:32616, WGS84 bounds approx -86.9445, 41.4440)
TEST_TIF_CENTER_LON = -86.94447585281846
TEST_TIF_CENTER_LAT = 41.44403702360668
# Point within UTM Zone 16N but well outside the raster footprint
TEST_TIF_OUTSIDE_LON = -87.5
TEST_TIF_OUTSIDE_LAT = 41.0

PNG_BYTES = b"\x89PNG\r\n\x1a\n"


def test_read_public_data_product_bounds(client: TestClient, db: Session):
    # create data product owned by random user
    data_product = SampleDataProduct(db)
    # make data product public
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    file_permission_in = FilePermissionUpdate(is_public=True)
    crud.file_permission.update(db, db_obj=file_permission, obj_in=file_permission_in)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "bounds" in response_data
    response_data["bounds"] == [
        -86.94452647774037,
        41.44399199810876,
        -86.94442522789655,
        41.44408204910461,
    ]


def test_read_projected_data_product_bounds(client: TestClient, db: Session):
    # create data product owned by random user
    data_product = SampleDataProduct(db)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_projected_data_product_bounds_with_authorized_user(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # create data product owned by logged in user
    data_product = SampleDataProduct(db, user=current_user)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "bounds" in response_data
    response_data["bounds"] == [
        -86.94452647774037,
        41.44399199810876,
        -86.94442522789655,
        41.44408204910461,
    ]


def test_read_data_product_point_value(client: TestClient, db: Session):
    """Public data product sampled at raster center returns a numeric value."""
    data_product = SampleDataProduct(db)
    # make data product public
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=FilePermissionUpdate(is_public=True)
    )
    response = client.get(
        f"{settings.API_V1_STR}/public/point"
        f"?data_product_id={data_product.obj.id}"
        f"&lon={TEST_TIF_CENTER_LON}&lat={TEST_TIF_CENTER_LAT}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "coordinates" in response_data
    assert "values" in response_data
    assert len(response_data["values"]) == 1
    assert response_data["values"][0] is not None
    assert isinstance(response_data["values"][0], float)


def test_read_data_product_point_value_outside_footprint(
    client: TestClient, db: Session
):
    """Sampling outside the raster footprint returns null (nodata) for all bands."""
    data_product = SampleDataProduct(db)
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=FilePermissionUpdate(is_public=True)
    )
    response = client.get(
        f"{settings.API_V1_STR}/public/point"
        f"?data_product_id={data_product.obj.id}"
        f"&lon={TEST_TIF_OUTSIDE_LON}&lat={TEST_TIF_OUTSIDE_LAT}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["values"] == [None]


def test_read_data_product_point_value_not_found(client: TestClient, db: Session):
    """Non-public data product without authentication returns 404."""
    data_product = SampleDataProduct(db)
    response = client.get(
        f"{settings.API_V1_STR}/public/point"
        f"?data_product_id={data_product.obj.id}"
        f"&lon={TEST_TIF_CENTER_LON}&lat={TEST_TIF_CENTER_LAT}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_data_product_point_value_authorized_user(
    client: TestClient, db: Session, normal_user_access_token: str
):
    """Data product owner can sample even when the product is not public."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    data_product = SampleDataProduct(db, user=current_user)
    response = client.get(
        f"{settings.API_V1_STR}/public/point"
        f"?data_product_id={data_product.obj.id}"
        f"&lon={TEST_TIF_CENTER_LON}&lat={TEST_TIF_CENTER_LAT}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["values"][0] is not None


def test_read_data_product_point_value_non_raster(client: TestClient, db: Session):
    """Non-raster data products return 400."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=FilePermissionUpdate(is_public=True)
    )
    response = client.get(
        f"{settings.API_V1_STR}/public/point"
        f"?data_product_id={data_product.obj.id}"
        f"&lon={TEST_TIF_CENTER_LON}&lat={TEST_TIF_CENTER_LAT}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_access_returns_liked_true_for_member_who_liked(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A member opening their own (private) liked data product sees liked=True."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Owned by the current user, not public.
    data_product = SampleDataProduct(db, user=current_user)
    create_data_product_like(
        db, data_product_id=data_product.obj.id, user_id=current_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/public/user_access?file_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["liked"] is True


def test_user_access_returns_liked_false_when_not_liked(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """The same access path reports liked=False when the user has not liked it."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    data_product = SampleDataProduct(db, user=current_user)

    response = client.get(
        f"{settings.API_V1_STR}/public/user_access?file_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["liked"] is False


def _make_data_product_public(db: Session, data_product: SampleDataProduct) -> None:
    """Grant public access to a sample data product."""
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=FilePermissionUpdate(is_public=True)
    )


def _mock_tile_response(
    status_code: int = 200, content: bytes = PNG_BYTES, text: str = ""
) -> MagicMock:
    """Create a mock titiler tile response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.content = content
    mock_response.text = text
    return mock_response


def _mock_titiler_client(
    mock_async_client_cls: MagicMock, mock_response: Optional[MagicMock] = None
) -> AsyncMock:
    """Wire an AsyncMock httpx client onto a patched AsyncClient class."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response or _mock_tile_response())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client
    return mock_client


def _requested_tile_query(mock_client: AsyncMock) -> Dict[str, List[str]]:
    """Return the query parameters titiler was asked for."""
    return parse_qs(urlsplit(mock_client.get.call_args.args[0]).query)


@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_requests_titiler_tilesize_url(
    mock_async_client_cls: MagicMock, client: TestClient, db: Session
) -> None:
    """Tiles are requested with the tilesize parameter TiTiler 2.x expects."""
    data_product = SampleDataProduct(db)
    _make_data_product_public(db, data_product)
    mock_client = _mock_titiler_client(mock_async_client_cls)

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}"
        "&scale=2&bidx=1&rescale=0,255&colormap_name=viridis"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
    assert response.content == PNG_BYTES
    mock_client.get.assert_called_once()
    assert mock_client.get.call_args.kwargs["timeout"] == 30.0

    tile_url = urlsplit(mock_client.get.call_args.args[0])
    assert tile_url.netloc == "varnish"
    assert tile_url.path == "/cog/tiles/WebMercatorQuad/12/1049/1533"

    query = parse_qs(tile_url.query)
    assert query["tilesize"] == ["512"]
    assert query["url"] == [data_product.obj.filepath]
    assert query["bidx"] == ["1"]
    assert query["rescale"] == ["0,255"]
    assert query["colormap_name"] == ["viridis"]
    assert query["dataProductId"] == [str(data_product.obj.id)]
    assert "expires" in query
    assert "secure" in query


@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_forwards_repeated_multiband_params(
    mock_async_client_cls: MagicMock, client: TestClient, db: Session
) -> None:
    """Repeated bidx and rescale values survive query string encoding."""
    data_product = SampleDataProduct(db)
    _make_data_product_public(db, data_product)
    mock_client = _mock_titiler_client(mock_async_client_cls)

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}&scale=2"
        "&bidx=3&bidx=2&bidx=1"
        "&rescale=0,255&rescale=10,200&rescale=20,180"
    )

    assert response.status_code == status.HTTP_200_OK
    query = _requested_tile_query(mock_client)
    assert query["bidx"] == ["3", "2", "1"]
    assert query["rescale"] == ["0,255", "10,200", "20,180"]
    assert "colormap_name" not in query


@pytest.mark.parametrize(
    "scale,tilesize", [(1, "256"), (2, "512"), (3, "768"), (4, "1024")]
)
@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_scale_sets_tilesize(
    mock_async_client_cls: MagicMock,
    client: TestClient,
    db: Session,
    scale: int,
    tilesize: str,
) -> None:
    """Each supported scale maps onto a multiple of the 256px tile matrix size."""
    data_product = SampleDataProduct(db)
    _make_data_product_public(db, data_product)
    mock_client = _mock_titiler_client(mock_async_client_cls)

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}&scale={scale}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert _requested_tile_query(mock_client)["tilesize"] == [tilesize]


@pytest.mark.parametrize("params", ["scale=0", "scale=5", "scale=2&x=1.5"])
@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_rejects_invalid_params(
    mock_async_client_cls: MagicMock, client: TestClient, db: Session, params: str
) -> None:
    """Out of range scales and non-integer tile coordinates are rejected."""
    data_product = SampleDataProduct(db)
    _make_data_product_public(db, data_product)

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}&{params}"
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mock_async_client_cls.assert_not_called()


@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_not_found_without_access(
    mock_async_client_cls: MagicMock, client: TestClient, db: Session
) -> None:
    """A data product without public access is never requested from titiler."""
    data_product = SampleDataProduct(db)

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}&scale=2"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_async_client_cls.assert_not_called()


@patch("app.api.api_v1.endpoints.public.httpx.AsyncClient")
def test_read_map_tiles_propagates_titiler_error(
    mock_async_client_cls: MagicMock, client: TestClient, db: Session
) -> None:
    """A titiler failure is surfaced with its status code."""
    data_product = SampleDataProduct(db)
    _make_data_product_public(db, data_product)
    _mock_titiler_client(
        mock_async_client_cls,
        _mock_tile_response(status_code=500, content=b"", text="boom"),
    )

    response = client.get(
        f"{settings.API_V1_STR}/public/maptiles"
        f"?z=12&x=1049&y=1533&data_product_id={data_product.obj.id}&scale=2"
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Error: boom"
