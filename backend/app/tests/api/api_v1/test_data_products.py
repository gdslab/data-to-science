from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from geojson_pydantic import Feature, FeatureCollection
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_metadata import (
    create_zonal_metadata,
    get_zonal_feature_collection,
)
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.flight import create_flight
from app.tests.utils.user import create_user
from app.tests.utils.vector_layers import (
    create_vector_layer_with_provided_feature_collection,
)
from app.utils.ColorBar import create_outfilename


def test_read_data_product_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert str(data_product.obj.id) == response_data_product["id"]
    assert "data_type" in response_data_product
    assert "flight_id" in response_data_product
    assert "original_filename" in response_data_product
    assert "stac_properties" in response_data_product
    assert "url" in response_data_product
    assert "status" in response_data_product
    assert "user_style" in response_data_product


def test_read_data_product_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)


def test_read_data_product_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)


def test_read_data_product_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_public_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    assert file_permission
    file_permission_in_update = FilePermissionUpdate(is_public=True)
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )
    response = client.get(f"{settings.API_V1_STR}/public?file_id={data_product.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.id)


def test_read_restricted_data_product_with_public_url(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db).obj
    response = client.get(f"{settings.API_V1_STR}/public?file_id={data_product.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_data_product_colorbar_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/utils/colorbar?cmin=100&cmax=200&cmap=terrain&refresh=false"
    )
    colorbar_filename = create_outfilename(100, 200, "terrain")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "colorbar_url" in response_data
    assert response_data["colorbar_url"] == (
        f"{settings.TEST_STATIC_DIR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/colorbars/{colorbar_filename}"
    )


def test_fetching_shortened_url_for_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create data product owned by current user
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(
        db, data_type="dsm", create_style=True, user=current_user
    )
    # Example share map URL
    original_url = f"http://localhost:8000/sharemap?file_id={data_product.obj.id}&symbology=eyJtYXgiOjUyLjUxNCwibWluIjotNC4xMDcsIm1vZGUiOiJtaW5NYXgiLCJ1c2VyTWF4Ijo1Mi41MTQsInVzZXJNaW4iOi00LjEwNywiY29sb3JSYW1wIjoicmFpbmJvdyIsIm1lYW5TdGREZXYiOjIsIm9wYWNpdHkiOjEwMH0="
    # Send request to shorten URL
    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/utils/shorten",
        json={"url": original_url},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "shortened_url" in response_data


def test_generate_data_product_colorbar_with_invalid_parameters(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/utils/colorbar?cmin=100&cmax=200&cmap=invalid-cmap&refresh=false"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_read_data_products_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=current_user,
        )
    SampleDataProduct(db)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_products = response.json()
    assert type(response_data_products) is list
    assert len(response_data_products) == 3
    for data_product in response_data_products:
        assert data_product["flight_id"] == str(flight.id)
        assert "data_type" in data_product
        assert "flight_id" in data_product
        assert "original_filename" in data_product
        assert "stac_properties" in data_product
        assert "url" in data_product
        assert "user_style" in data_product


def test_read_data_products_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_products = response.json()
    assert type(response_data_products) is list
    assert len(response_data_products) == 3
    for data_product in response_data_products:
        assert data_product["flight_id"] == str(flight.id)
        assert "data_type" in data_product
        assert "flight_id" in data_product
        assert "original_filename" in data_product
        assert "stac_properties" in data_product
        assert "url" in data_product
        assert "user_style" in data_product


def test_read_data_products_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_products = response.json()
    assert type(response_data_products) is list
    assert len(response_data_products) == 3
    for data_product in response_data_products:
        assert data_product["flight_id"] == str(flight.id)
        assert "data_type" in data_product
        assert "flight_id" in data_product
        assert "original_filename" in data_product
        assert "stac_properties" in data_product
        assert "url" in data_product
        assert "user_style" in data_product


def test_read_data_products_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_data_product_bands_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # New band description
    bands_in = [{"name": "b1", "description": "Blue"}]
    # Create sample data product with user owned project
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)
    assert response_data_product["stac_properties"]["eo"] == bands_in


def test_update_data_product_bands_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # New band description
    bands_in = [{"name": "b1", "description": "Blue"}]
    # Create sample data product with user in project manager role
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)
    assert response_data_product["stac_properties"]["eo"] == bands_in


def test_update_data_product_bands_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # New band description
    bands_in = [{"name": "b1", "description": "Blue"}]
    # Create sample data product with user in project viewer role
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_data_product_bands_without_project_role(
    client: TestClient, db: Session
) -> None:
    # New band description
    bands_in = [{"name": "b1", "description": "Blue"}]
    # Create sample data product with user in no project role
    project = create_project(db)
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_data_product_bands_with_incorrect_band_name(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # New band description with incorrect band name (should be "b1")
    bands_in = [{"name": "b3", "description": "Blue"}]
    # Create sample data product with user owned project
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_data_product_bands_with_too_many_band_names(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # New band description with incorrect band name (should be "b1")
    bands_in = [
        {"name": "b1", "description": "Alpha"},
        {"name": "b2", "description": "Gray"},
    ]
    # Create sample data product with user owned project
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, project=project)
    # Create payload for updating bands
    payload = {"bands": bands_in}
    # Send request to update bands
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/bands",
        json=payload,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_data_product_data_type_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    old_data_type = "dsm"
    new_data_type = "dtm"
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, data_type=old_data_type, project=project)
    payload = {"data_type": new_data_type}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)
    assert response_data_product["data_type"] == new_data_type


def test_update_data_product_data_type_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    old_data_type = "dsm"
    new_data_type = "dtm"
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    data_product = SampleDataProduct(db, data_type=old_data_type, project=project)
    # add current user as a manager to the data product's project
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    payload = {"data_type": new_data_type}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}",
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)
    assert response_data_product["data_type"] == new_data_type


def test_update_data_product_data_type_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    old_data_type = "dsm"
    new_data_type = "dtm"
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    data_product = SampleDataProduct(db, data_type=old_data_type, project=project)
    # add current user as a viewer to the data product's project
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    payload = {"data_type": new_data_type}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}",
        json=payload,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_data_product_data_type_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    old_data_type = "dsm"
    new_data_type = "dtm"
    project = create_project(db)
    data_product = SampleDataProduct(db, data_type=old_data_type, project=project)
    payload = {"data_type": new_data_type}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}",
        json=payload,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_data_product_with_point_cloud_data_type(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    old_data_type = "point_cloud"
    new_data_type = "dtm"
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, data_type=old_data_type, project=project)
    payload = {"data_type": new_data_type}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}",
        json=payload,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_deactivate_data_product_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    deactivated_data_product = response.json()
    assert deactivated_data_product
    assert deactivated_data_product.get("id", None) == str(data_product.obj.id)
    assert deactivated_data_product.get("is_active", True) is False
    deactivated_at = datetime.strptime(
        deactivated_data_product.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)


def test_deactivate_data_product_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        role="manager",
        member_id=current_user.id,
        project_id=data_product.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_data_product_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        role="viewer",
        member_id=current_user.id,
        project_id=data_product.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_data_product_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db, create_style=True)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_running_tool_on_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    rgb_data_product = SampleDataProduct(
        db, data_type="ortho", multispectral=True, user=current_user
    )
    processing_request = {
        "chm": False,
        "exg": True,
        "exgRed": 3,
        "exgGreen": 2,
        "exgBlue": 1,
        "ndvi": False,
        "ndviNIR": 4,
        "ndviRed": 3,
        "zonal": False,
        "zonal_layer_id": "",
    }

    response = client.post(
        f"{settings.API_V1_STR}/projects/{rgb_data_product.project.id}"
        f"/flights/{rgb_data_product.flight.id}/data_products/{rgb_data_product.obj.id}/tools",
        json=processing_request,
    )
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_get_zonal_statistics(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create project, add current user as viewer in project, and add data product
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    data_product = SampleDataProduct(db, data_type="dsm", project=project)
    # get single polygon feature inside the sample data product
    zone_feature = get_zonal_feature_collection(single_feature=True)
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db,
        feature_collection=FeatureCollection(
            **{"type": "FeatureCollection", "features": [zone_feature]}
        ),
        project_id=project.id,
    )
    # mock the celery task initiated by the endpoint
    with patch(
        "app.tasks.toolbox_tasks.calculate_zonal_statistics.apply_async"
    ) as mock_apply_async:
        mock_task = MagicMock()
        mock_task.id = "mock_task_id"
        mock_task.get.return_value = [
            {
                "min": 187.37115478515625,
                "max": 187.4439239501953,
                "mean": 187.40421549479166,
                "count": 576,
                "std": 0.013546454430626641,
                "median": 187.4020233154297,
            }
        ]

        mock_apply_async.return_value = mock_task
        # request zonal statistics for zone and sample data product
        response = client.post(
            f"{settings.API_V1_STR}/projects/{project.id}/flights/{data_product.flight.id}"
            f"/data_products/{data_product.obj.id}/zonal_statistics",
            json=vector_layer.features[0].model_dump(),
        )
        mock_apply_async.assert_called_once_with(
            args=(
                data_product.obj.filepath,
                {"features": [vector_layer.features[0].model_dump()]},
            )
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert Feature(**response_data)
        response_feature = Feature(**response_data)
        assert (
            response_feature.properties["min"]
            and response_feature.properties["max"]
            and response_feature.properties["mean"]
            and response_feature.properties["count"]
            and response_feature.properties["median"]
            and response_feature.properties["std"]
        )
        # check that original feature collection properties are present
        properties = ["row", "col"]
        for key in properties:
            assert key in response_feature.properties


def test_get_zonal_statistics_by_layer_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create project, add current user as viewer in project, and add data product
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    data_product = SampleDataProduct(db, data_type="dsm", project=project)
    # create zonal statistics metadata for data product
    zonal_metadata, layer_id, properties = create_zonal_metadata(
        db, data_product_id=data_product.obj.id, project_id=project.id
    )
    # request zonal statistics by layer id for a data product
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/zonal_statistics?layer_id={layer_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert FeatureCollection(**response_data)
    response_feature_collection: FeatureCollection = FeatureCollection(**response_data)
    assert len(response_feature_collection.features) == len(zonal_metadata)
    # check that zonal stats are present for first feature in list
    response_first_feature = response_feature_collection.features[0]
    assert (
        response_first_feature.properties["min"]
        and response_first_feature.properties["max"]
        and response_first_feature.properties["mean"]
        and response_first_feature.properties["count"]
        and response_first_feature.properties["median"]
        and response_first_feature.properties["std"]
    )
    # check that original feature collection properties are present
    for key in properties:
        assert key in response_first_feature.properties
