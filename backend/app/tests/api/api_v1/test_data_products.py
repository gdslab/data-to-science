import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from geojson_pydantic import Feature, FeatureCollection
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import get_current_user
from app.core import security
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.schemas.job import Status as JobStatus
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_metadata import (
    create_xml_metadata,
    create_zonal_metadata,
    get_sample_xml_filepath,
    get_zonal_feature_collection,
)
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user
from app.tests.utils.vector_layers import (
    create_feature_collection,
    create_vector_layer_with_provided_feature_collection,
)
from app.utils import raster_export
from app.utils.ColorBar import create_outfilename
from app.utils.ImageProcessor import get_info, get_stac_properties


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


def test_read_data_product_with_mismatched_flight_returns_403(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # IDOR guard: a flight the user owns in the path must not grant access to a
    # data product that belongs to a different flight.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    other_flight = create_flight(db, project_id=data_product.project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{other_flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_data_product_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
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
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
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
    get_current_user(db, normal_user_access_token)
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
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
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
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
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
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
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
        project_uuid=project.id,
        role=Role.MANAGER,
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
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
        project_uuid=project.id,
        role=Role.VIEWER,
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
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
    get_current_user(db, normal_user_access_token)
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
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
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
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
    assert deactivated_data_product is not None
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
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
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
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
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


def test_deactivate_data_product_when_project_is_published(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)

    # Publish the project (sets is_published=True)
    crud.project.update_project_visibility(
        db, project_id=data_product.project.id, is_public=True
    )

    # Verify the project is published
    published_project = crud.project.get(db, id=data_product.project.id)
    assert published_project is not None
    assert published_project.is_published is True

    # Attempt to deactivate the data product
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def get_data_product_xml_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/xml"
    )


def read_sample_xml_bytes() -> bytes:
    with open(get_sample_xml_filepath(), "rb") as xml_file:
        return xml_file.read()


def test_upload_data_product_xml_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_metadata = response.json()
    assert response_metadata["category"] == "xml"
    assert response_metadata["data_product_id"] == str(data_product.obj.id)
    assert response_metadata["properties"]["original_filename"] == "sample.xml"
    assert os.path.exists(response_metadata["properties"]["filepath"])


def test_upload_data_product_xml_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
    )
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_upload_data_product_xml_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
    )
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_upload_data_product_xml_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_upload_data_product_xml_with_malformed_xml(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", b"<metadata><unclosed></metadata>", "text/xml")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_upload_data_product_xml_with_wrong_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.txt", read_sample_xml_bytes(), "text/plain")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_upload_data_product_xml_when_xml_already_exists(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    create_xml_metadata(db, data_product_id=data_product.obj.id)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_upload_data_product_xml_with_unsupported_data_type(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    for data_type in ["panoramic", "3dgs"]:
        data_product = SampleDataProduct(db, data_type=data_type, user=current_user)
        response = client.post(
            get_data_product_xml_url(data_product),
            files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_upload_data_product_xml_with_point_cloud_data_type(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="point_cloud", user=current_user)
    response = client.post(
        get_data_product_xml_url(data_product),
        files={"file": ("sample.xml", read_sample_xml_bytes(), "text/xml")},
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_read_data_product_includes_xml_metadata(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    create_xml_metadata(db, data_product_id=data_product.obj.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["xml_metadata"] is not None
    assert response_data_product["xml_metadata"]["original_filename"] == "sample.xml"
    assert response_data_product["xml_metadata"][
        "content"
    ] == read_sample_xml_bytes().decode("utf-8")


def test_read_data_products_includes_xml_metadata(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(
        db, flight=flight, project=project, user=current_user
    )
    SampleDataProduct(db, flight=flight, project=project, user=current_user)
    create_xml_metadata(db, data_product_id=data_product.obj.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_products = response.json()
    assert len(response_data_products) == 2
    for response_data_product in response_data_products:
        if response_data_product["id"] == str(data_product.obj.id):
            assert response_data_product["xml_metadata"] is not None
            assert (
                response_data_product["xml_metadata"]["original_filename"]
                == "sample.xml"
            )
        else:
            assert response_data_product["xml_metadata"] is None


def test_delete_data_product_xml_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    metadata = create_xml_metadata(db, data_product_id=data_product.obj.id)
    xml_filepath = metadata.properties["filepath"]
    assert os.path.exists(xml_filepath)
    response = client.delete(get_data_product_xml_url(data_product))
    assert response.status_code == status.HTTP_200_OK
    response_metadata = response.json()
    assert response_metadata["id"] == str(metadata.id)
    assert not os.path.exists(xml_filepath)
    assert crud.data_product_metadata.get(db, id=metadata.id) is None


def test_delete_data_product_xml_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
    )
    create_xml_metadata(db, data_product_id=data_product.obj.id)
    response = client.delete(get_data_product_xml_url(data_product))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_data_product_xml_when_no_xml_exists(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.delete(get_data_product_xml_url(data_product))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def get_processing_request(**overrides: Any) -> dict:
    """Return a processing tool request payload with no tools selected.

    Keyword arguments override individual fields (e.g., zonal=True).
    """
    processing_request = {
        "chm": False,
        "chmResolution": 0.5,
        "chmPercentile": 98,
        "dem_id": None,
        "dtm": False,
        "dtmResolution": 0.5,
        "dtmRigidness": 2,
        "exg": False,
        "exgRed": 3,
        "exgGreen": 2,
        "exgBlue": 1,
        "hillshade": False,
        "ndvi": False,
        "ndviNIR": 4,
        "ndviRed": 3,
        "vari": False,
        "variRed": 3,
        "variGreen": 2,
        "variBlue": 1,
        "zonal": False,
        "zonal_layer_id": "",
    }
    processing_request.update(overrides)
    return processing_request


def get_tools_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/tools"
    )


def test_running_tool_on_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    rgb_data_product = SampleDataProduct(
        db, data_type="ortho", multispectral=True, user=current_user
    )
    processing_request = get_processing_request(exg=True, vari=True)

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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
        response_feature: Feature = Feature(**response_data)
        assert response_feature.properties is not None
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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


def test_running_zonal_tool_on_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    zones = get_zonal_feature_collection()
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=zones, project_id=data_product.project.id
    )
    layer_id = vector_layer.features[0].properties["layer_id"]

    with patch(
        "app.tasks.toolbox_tasks.calculate_bulk_zonal_statistics.apply_async"
    ) as mock_apply_async:
        response = client.post(
            get_tools_url(data_product),
            json=get_processing_request(zonal=True, zonal_layer_id=layer_id),
        )

    assert response.status_code == status.HTTP_202_ACCEPTED
    response_jobs = response.json()["jobs"]
    assert len(response_jobs) == 1
    assert response_jobs[0]["name"] == "zonal"
    assert response_jobs[0]["layer_id"] == layer_id

    # job record created with layer id in extra
    job = crud.job.get(db, id=UUID(response_jobs[0]["id"]))
    assert job is not None
    assert job.status == JobStatus.WAITING
    assert job.extra == {"layer_id": layer_id}
    assert job.data_product_id == data_product.obj.id

    # task dispatched with raster path, data product id, features, and job id
    mock_apply_async.assert_called_once()
    task_args = mock_apply_async.call_args.kwargs["args"]
    assert task_args[0] == data_product.obj.filepath
    assert task_args[1] == data_product.obj.id
    assert len(task_args[2]["features"]) == len(vector_layer.features)
    assert task_args[3] == job.id


def test_running_zonal_tool_without_layer_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    response = client.post(
        get_tools_url(data_product),
        json=get_processing_request(zonal=True, zonal_layer_id=""),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_running_zonal_tool_with_unknown_layer_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    response = client.post(
        get_tools_url(data_product),
        json=get_processing_request(zonal=True, zonal_layer_id="nonexistent"),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_running_zonal_tool_with_layer_from_other_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    other_project = create_project(db)
    zones = get_zonal_feature_collection()
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=zones, project_id=other_project.id
    )
    layer_id = vector_layer.features[0].properties["layer_id"]
    response = client.post(
        get_tools_url(data_product),
        json=get_processing_request(zonal=True, zonal_layer_id=layer_id),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_running_zonal_tool_with_non_polygon_layer(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    point_layer = create_feature_collection(
        db, "point", project_id=data_product.project.id
    )
    layer_id = point_layer.features[0].properties["layer_id"]
    response = client.post(
        get_tools_url(data_product),
        json=get_processing_request(zonal=True, zonal_layer_id=layer_id),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_running_tool_with_no_product_selected(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    response = client.post(get_tools_url(data_product), json=get_processing_request())
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_running_tool_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm")
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
    )
    response = client.post(
        get_tools_url(data_product), json=get_processing_request(hillshade=True)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_data_product_jobs(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    zonal_job = create_job(
        db,
        data_product_id=data_product.obj.id,
        name="zonal",
        extra={"layer_id": "abc12345"},
    )
    create_job(db, data_product_id=data_product.obj.id, name="hillshade")

    url = (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/jobs"
    )

    # all jobs for data product (SampleDataProduct also creates an upload job)
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_job_names = [job["name"] for job in response.json()]
    assert "zonal" in response_job_names
    assert "hillshade" in response_job_names

    # filtered by job name
    response = client.get(url, params={"name": "zonal"})
    assert response.status_code == status.HTTP_200_OK
    response_jobs = response.json()
    assert len(response_jobs) == 1
    assert response_jobs[0]["id"] == str(zonal_job.id)
    assert response_jobs[0]["name"] == "zonal"
    assert response_jobs[0]["status"] == "WAITING"
    assert response_jobs[0]["extra"] == {"layer_id": "abc12345"}


def test_read_data_product_jobs_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    create_job(db, data_product_id=data_product.obj.id, name="zonal")
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/jobs"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_data_product_jobs_with_data_product_from_other_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A data product id from another project must not be readable through a
    flight the user can access.
    """
    current_user = get_current_user(db, normal_user_access_token)
    own_data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    other_data_product = SampleDataProduct(db, data_type="dsm")
    create_job(db, data_product_id=other_data_product.obj.id, name="zonal")
    response = client.get(
        f"{settings.API_V1_STR}/projects/{own_data_product.project.id}"
        f"/flights/{own_data_product.flight.id}"
        f"/data_products/{other_data_product.obj.id}/jobs"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_zonal_statistics_ignores_feature_id_not_in_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A stale feature_id embedded in the submitted zone (e.g., from a
    re-uploaded export) that does not resolve to a vector layer in this
    project must trigger a fresh computation for the submitted geometry
    instead of returning another feature's cached stats.
    """
    current_user = get_current_user(db, normal_user_access_token)
    # cached zonal stats for a feature that lives in a different project
    other_project = create_project(db)
    other_data_product = SampleDataProduct(db, data_type="dsm", project=other_project)
    other_metadata, _, _ = create_zonal_metadata(
        db, data_product_id=other_data_product.obj.id, project_id=other_project.id
    )
    foreign_feature_id = str(other_metadata[0].vector_layer_feature_id)

    # current user's own project and data product
    data_product = SampleDataProduct(db, data_type="dsm", user=current_user)
    zone_feature = get_zonal_feature_collection(single_feature=True)
    zone_dict = zone_feature.model_dump()
    zone_dict["properties"] = {
        **(zone_dict.get("properties") or {}),
        "feature_id": foreign_feature_id,
    }

    mocked_stats = {
        "min": 187.371,
        "max": 187.444,
        "mean": 187.404,
        "count": 576,
        "std": 0.0135,
        "median": 187.402,
    }
    with patch(
        "app.tasks.toolbox_tasks.calculate_zonal_statistics.apply_async"
    ) as mock_apply_async:
        mock_task = MagicMock()
        mock_task.get.return_value = [mocked_stats]
        mock_apply_async.return_value = mock_task
        response = client.post(
            f"{settings.API_V1_STR}/projects/{data_product.project.id}"
            f"/flights/{data_product.flight.id}"
            f"/data_products/{data_product.obj.id}/zonal_statistics",
            json=zone_dict,
        )

    assert response.status_code == status.HTTP_200_OK
    # a fresh computation ran; the foreign cache was not used
    mock_apply_async.assert_called_once()
    response_feature = Feature(**response.json())
    assert response_feature.properties is not None
    assert response_feature.properties["mean"] == mocked_stats["mean"]
    # the submitted geometry is returned, not the foreign feature's geometry
    assert response_feature.geometry == zone_feature.geometry
    # no metadata cached against the foreign feature id for this data product
    metadata = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=data_product.obj.id,
        vector_layer_feature_id=other_metadata[0].vector_layer_feature_id,
    )
    assert len(metadata) == 0


def test_create_from_ext_storage_stores_per_job_report(
    client: TestClient, db: Session, tmp_path, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=JobStatus.INPROGRESS,
        extra={"backend": "odm", "settings": {"orthoResolution": 4.0}},
    )
    # single-use token for the raw data owner
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=schemas.SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="rawdata")
        ),
        user_id=raw_data.user.id,
    )
    # report produced by the external processing service
    remote_report = tmp_path / "report.pdf"
    remote_report.write_bytes(b"%PDF-1.4 test report")

    payload = {
        "token": token,
        "job_id": str(job.id),
        "status": {"code": 1, "message": "completed"},
        "products": [],
        "report": {
            "filename": "report.pdf",
            "storage_path": str(remote_report),
            "raw_data_id": str(raw_data.obj.id),
        },
    }
    with patch("app.utils.job_manager.get_db", side_effect=lambda: iter([db])):
        response = client.post(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/data_products/create_from_ext_storage",
            json=payload,
        )
    assert response.status_code == status.HTTP_202_ACCEPTED

    # report copied with per-job filename
    expected_report = Path(raw_data.obj.filepath).parent / f"report_{job.id}.pdf"
    assert expected_report.exists()
    assert expected_report.read_bytes() == b"%PDF-1.4 test report"

    # job marked successful with report path merged into existing extra
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == JobStatus.SUCCESS
    assert updated_job.extra["report"] == str(expected_report)
    assert updated_job.extra["settings"] == {"orthoResolution": 4.0}

    # jobs endpoint composes the absolute report URL at read time
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/jobs"
    )
    assert response.status_code == status.HTTP_200_OK
    response_job = next(j for j in response.json() if j["id"] == str(job.id))
    assert response_job["extra"]["report"] == (
        f"{settings.API_DOMAIN}{expected_report}"
    )


def test_create_from_ext_storage_links_products_to_raw_data(
    client: TestClient, db: Session, tmp_path, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=JobStatus.INPROGRESS,
        extra={"backend": "odm", "settings": {"orthoResolution": 4.0}},
    )
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=schemas.SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="rawdata")
        ),
        user_id=raw_data.user.id,
    )
    # data product produced by the external processing service
    product_file = tmp_path / "ortho.tif"
    product_file.write_bytes(b"fake tif")

    payload = {
        "token": token,
        "job_id": str(job.id),
        "status": {"code": 1, "message": "completed"},
        "products": [
            {
                "data_type": "ortho",
                "filename": "ortho.tif",
                "storage_path": str(product_file),
            }
        ],
        "report": None,
    }
    with (
        patch(
            "app.utils.tusd.post_processing.upload_geotiff.apply_async"
        ) as mock_apply,
        patch("app.utils.job_manager.get_db", side_effect=lambda: iter([db])),
    ):
        response = client.post(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/data_products/create_from_ext_storage",
            json=payload,
        )
    assert response.status_code == status.HTTP_202_ACCEPTED
    # the post-processing celery task was dispatched for the product
    mock_apply.assert_called_once()

    # job marked successful with outputs recorded and existing extra preserved
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == JobStatus.SUCCESS
    assert updated_job.extra["settings"] == {"orthoResolution": 4.0}
    outputs = updated_job.extra["data_products"]
    assert len(outputs) == 1
    assert outputs[0]["data_type"] == "ortho"

    # the created data product links back to the source raw data
    created = crud.data_product.get(db, id=UUID(outputs[0]["id"]))
    assert created is not None
    assert created.raw_data_id == raw_data.obj.id


def test_read_data_products_includes_raw_data_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user, data_type="ortho")
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
    products = response.json()
    match = next(p for p in products if p["id"] == str(data_product.obj.id))
    # directly uploaded products carry no raw data source
    assert match["raw_data_id"] is None


def get_export_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/export/jpeg"
    )


def test_export_data_product_to_jpeg_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_export_data_product_to_jpeg_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    data_product = SampleDataProduct(db, project=project)
    response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_export_data_product_to_jpeg_with_symbology_settings(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    stats = data_product.obj.stac_properties["raster"][0]["stats"]
    settings_in = {
        "colorRamp": "viridis",
        "meanStdDev": 2,
        "mode": "minMax",
        "opacity": 100,
        "min": stats["minimum"],
        "max": stats["maximum"],
        "userMin": stats["minimum"],
        "userMax": stats["maximum"],
    }
    styled_response = client.post(
        get_export_url(data_product), json={"settings": settings_in}
    )
    assert styled_response.status_code == status.HTTP_200_OK
    assert styled_response.headers["content-type"] == "image/jpeg"

    # the styled export applies a color ramp, so it differs from the raw export
    raw_response = client.post(get_export_url(data_product), json={})
    assert raw_response.status_code == status.HTTP_200_OK
    assert styled_response.content != raw_response.content


def test_export_data_product_to_jpeg_with_unknown_color_ramp(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(
        get_export_url(data_product),
        json={"settings": {"colorRamp": "notARealColorRamp", "mode": "minMax"}},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_export_data_product_to_jpeg_with_point_cloud_data_type(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    data_product = SampleDataProduct(db, data_type="point_cloud", project=project)
    response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_export_data_product_to_jpeg_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_export_data_product_to_jpeg_names_file_without_original_filename(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id, title="Corn Trial 2024")
    data_product = SampleDataProduct(db, data_type="dsm", project=project)

    # the uploaded name is untrusted and must not reach the downloader
    crud.data_product.update(
        db,
        db_obj=data_product.obj,
        obj_in=schemas.DataProductUpdate(original_filename="../../evil name.tif"),
    )

    response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_200_OK

    content_disposition = response.headers["content-disposition"]
    acquisition_date = data_product.flight.acquisition_date.strftime("%Y%m%d")
    assert f"Corn_Trial_2024_{acquisition_date}_dsm.jpg" in content_disposition
    assert "evil" not in content_disposition
    assert ".." not in content_disposition


def test_read_data_product_returns_a_safe_download_filename(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id, title="Corn Trial 2024")
    data_product = SampleDataProduct(db, data_type="dsm", project=project)
    crud.data_product.update(
        db,
        db_obj=data_product.obj,
        obj_in=schemas.DataProductUpdate(original_filename="../../evil name.tif"),
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK

    acquisition_date = data_product.flight.acquisition_date.strftime("%Y%m%d")
    download_filename = response.json()["download_filename"]
    assert download_filename == f"Corn_Trial_2024_{acquisition_date}_dsm.tif"
    assert "evil" not in download_filename


@contextmanager
def capture_export_work_dir():
    """Records the temp directory an export creates so cleanup can be asserted.

    Listing the temp directory instead would be unreliable: the suite runs under
    xdist, so other tests create their own export directories alongside this one.
    """
    created: list = []
    make_work_dir = raster_export.create_export_work_dir

    def record() -> Path:
        work_dir = make_work_dir()
        created.append(work_dir)
        return work_dir

    with patch(
        "app.api.api_v1.endpoints.data_products.create_export_work_dir",
        side_effect=record,
    ):
        yield created


def test_export_data_product_to_jpeg_cleans_up_after_a_successful_export(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A finished export leaves nothing behind in the temp directory.

    Production mounts a tmpfs on /var/tmp, so anything left there is memory held
    until the container restarts.
    """
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    with capture_export_work_dir() as work_dirs:
        response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_200_OK

    assert len(work_dirs) == 1
    assert not work_dirs[0].exists()


def test_export_data_product_to_jpeg_cleans_up_after_a_failed_export(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A rejected export leaves nothing behind either.

    FastAPI only attaches background tasks to a returned Response, so cleanup
    registered before a raised HTTPException would never run.
    """
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    with capture_export_work_dir() as work_dirs:
        response = client.post(
            get_export_url(data_product),
            json={"settings": {"colorRamp": "notARealColorRamp", "mode": "minMax"}},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert len(work_dirs) == 1
    assert not work_dirs[0].exists()


def test_export_data_product_to_jpeg_cleans_up_after_a_server_error(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """An unexpected failure still cleans up the temp directory."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    with capture_export_work_dir() as work_dirs:
        with patch(
            "app.api.api_v1.endpoints.data_products.export_raster_to_jpeg",
            side_effect=RuntimeError("boom"),
        ):
            response = client.post(get_export_url(data_product), json={})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    assert len(work_dirs) == 1
    assert not work_dirs[0].exists()


@pytest.mark.parametrize(
    "settings_in",
    [
        pytest.param({"colorRamp": 5, "mode": "minMax"}, id="non-string color ramp"),
        pytest.param(
            {"colorRamp": "viridis", "mode": "minMax", "min": {}}, id="dict min"
        ),
        pytest.param(
            {"colorRamp": "viridis", "mode": "minMax", "min": "inf"},
            id="infinite min",
        ),
        pytest.param(
            {"colorRamp": "viridis", "mode": "minMax", "max": "nan"}, id="nan max"
        ),
        pytest.param(
            {"colorRamp": "viridis", "mode": "meanStdDev", "meanStdDev": []},
            id="list mean std dev",
        ),
        pytest.param(
            {"colorRamp": "viridis", "nodata": "--config CPL_DEBUG ON"},
            id="non-numeric nodata",
        ),
        pytest.param({"mode": "minMax"}, id="neither color ramp nor bands"),
    ],
)
def test_export_data_product_to_jpeg_rejects_malformed_settings(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    settings_in: dict,
) -> None:
    """Bad symbology values are refused up front rather than reaching GDAL.

    Every one of these used to raise deep inside the export and surface as a 500.
    """
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.post(get_export_url(data_product), json={"settings": settings_in})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_export_data_product_to_jpeg_accepts_settings_with_unknown_keys(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Keys the export does not use are ignored, not rejected.

    The map sends a whole background data product inside single band symbology.
    """
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    stats = data_product.obj.stac_properties["raster"][0]["stats"]

    response = client.post(
        get_export_url(data_product),
        json={
            "settings": {
                "colorRamp": "viridis",
                "mode": "minMax",
                "min": stats["minimum"],
                "max": stats["maximum"],
                "background": {"id": str(data_product.obj.id), "data_type": "dsm"},
            }
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/jpeg"


def test_export_data_product_to_jpeg_with_multiband_symbology(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """The multiband payload the map sends round-trips through the endpoint."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user, multispectral=True)
    stac_properties = get_stac_properties(get_info(Path(data_product.obj.filepath)))
    crud.data_product.update_bands(db, data_product.obj.id, stac_properties)

    def band(idx: int) -> dict:
        stats = stac_properties["raster"][idx - 1]["stats"]
        return {
            "idx": idx,
            "min": stats["minimum"],
            "max": stats["maximum"],
            "userMin": stats["minimum"],
            "userMax": stats["maximum"],
        }

    response = client.post(
        get_export_url(data_product),
        json={
            "settings": {
                "mode": "minMax",
                "meanStdDev": 2,
                "opacity": 100,
                "red": band(1),
                "green": band(2),
                "blue": band(3),
            }
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_export_data_product_to_jpeg_rejects_an_out_of_range_band_index(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A band index past the raster's band count is refused."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user, multispectral=True)
    stac_properties = get_stac_properties(get_info(Path(data_product.obj.filepath)))
    crud.data_product.update_bands(db, data_product.obj.id, stac_properties)

    band = {"idx": 1, "min": 0, "max": 255, "userMin": 0, "userMax": 255}
    response = client.post(
        get_export_url(data_product),
        json={
            "settings": {
                "mode": "minMax",
                "red": {**band, "idx": 99},
                "green": band,
                "blue": band,
            }
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_export_data_product_to_jpeg_without_stac_properties(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A data product with no band metadata is refused instead of raising a 500."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    crud.data_product.update_bands(db, data_product.obj.id, None)

    response = client.post(get_export_url(data_product), json={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_read_data_products_includes_a_safe_download_filename(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """The list endpoint carries the download name too.

    This is the endpoint the data products table and card views actually read.
    """
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id, title="Corn Trial 2024")
    data_product = SampleDataProduct(db, data_type="dsm", project=project)
    crud.data_product.update(
        db,
        db_obj=data_product.obj,
        obj_in=schemas.DataProductUpdate(original_filename="../../evil name.tif"),
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{data_product.flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK

    acquisition_date = data_product.flight.acquisition_date.strftime("%Y%m%d")
    match = next(
        product
        for product in response.json()
        if product["id"] == str(data_product.obj.id)
    )
    assert match["download_filename"] == f"Corn_Trial_2024_{acquisition_date}_dsm.tif"
    assert "evil" not in match["download_filename"]


def test_read_data_products_is_unaffected_by_raw_data_on_the_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A flight's raw data does not duplicate or drop rows in the list.

    Eager loading the flight to build the download name pulls Flight.raw_data
    along with it, because that relationship is lazy="joined". This is the shape
    that would surface it.
    """
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id, title="Corn Trial 2024")
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    data_products = [
        SampleDataProduct(db, data_type="dsm", project=project, flight=flight),
        SampleDataProduct(db, data_type="ortho", project=project, flight=flight),
    ]
    SampleRawData(db, project=project, flight=flight)
    SampleRawData(db, project=project, flight=flight)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK

    returned = response.json()
    returned_ids = [product["id"] for product in returned]
    assert sorted(returned_ids) == sorted(
        str(data_product.obj.id) for data_product in data_products
    )
    # one row per data product, not one per data product per raw data record
    assert len(returned_ids) == len(set(returned_ids))

    acquisition_date = flight.acquisition_date.strftime("%Y%m%d")
    assert {product["download_filename"] for product in returned} == {
        f"Corn_Trial_2024_{acquisition_date}_dsm.tif",
        f"Corn_Trial_2024_{acquisition_date}_ortho.tif",
    }
