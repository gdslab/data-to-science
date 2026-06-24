from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
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
    response_bounds = response_data["bounds"] == [
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
    response_bounds = response_data["bounds"] == [
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
