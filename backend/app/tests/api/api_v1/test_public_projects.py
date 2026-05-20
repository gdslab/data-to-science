import uuid

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file_permission import FilePermission
from app.models.project import Project as ProjectModel
from app.schemas.job import State, Status
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.project import create_project

API_URL = f"{settings.API_V1_STR}/public/projects"


def _publish(db: Session, project: ProjectModel) -> None:
    db.execute(
        sql_update(ProjectModel)
        .where(ProjectModel.id == project.id)
        .values(is_published=True)
    )
    db.commit()


def _deactivate(db: Session, project: ProjectModel) -> None:
    db.execute(
        sql_update(ProjectModel)
        .where(ProjectModel.id == project.id)
        .values(is_active=False)
    )
    db.commit()


def _make_data_product_public(db: Session, data_product_id: uuid.UUID) -> None:
    db.execute(
        sql_update(FilePermission)
        .where(FilePermission.file_id == data_product_id)
        .values(is_public=True)
    )
    db.commit()


# ---------------------------------------------------------------------------
# GET /public/projects
# ---------------------------------------------------------------------------


def test_read_published_projects_no_auth_returns_200(
    client: TestClient, db: Session
) -> None:
    response = client.get(API_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_read_published_projects_returns_only_active_published(
    client: TestClient, db: Session
) -> None:
    published_active = create_project(db)
    _publish(db, published_active)

    _unpublished_active = create_project(db)  # noqa: F841

    published_inactive = create_project(db)
    _publish(db, published_inactive)
    _deactivate(db, published_inactive)

    response = client.get(API_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    returned_ids = {item["id"] for item in data}
    assert str(published_active.id) in returned_ids
    assert str(published_inactive.id) not in returned_ids


def test_read_published_projects_geojson_format(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)

    response = client.get(API_URL, params={"format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)
    assert len(data["features"]) >= 1
    feature = next(f for f in data["features"] if f["properties"]["id"] == str(project.id))
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert feature["properties"]["title"] == project.title


# ---------------------------------------------------------------------------
# GET /public/projects/{project_id}
# ---------------------------------------------------------------------------


def test_read_published_project_returns_200(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)

    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project.id)
    assert data["title"] == project.title
    assert "centroid" in data
    assert "field" in data


def test_read_published_project_geojson_format(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)

    response = client.get(f"{API_URL}/{project.id}", params={"format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["geometry"]["type"] == "Polygon"


def test_read_published_project_unpublished_returns_404(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_published_project_inactive_returns_404(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)
    _deactivate(db, project)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_published_project_nonexistent_returns_404(
    client: TestClient, db: Session
) -> None:
    response = client.get(f"{API_URL}/{uuid.uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# GET /public/projects/{project_id}/flights
# ---------------------------------------------------------------------------


def test_read_published_project_flights_empty(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)

    response = client.get(f"{API_URL}/{project.id}/flights")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_read_published_project_flights_includes_public_data_products(
    client: TestClient, db: Session
) -> None:
    sample = SampleDataProduct(db, skip_job=True)
    create_job(
        db,
        data_product_id=sample.obj.id,
        name="upload-data-product",
        state=State.COMPLETED,
        status=Status.SUCCESS,
    )
    _publish(db, sample.project)
    _make_data_product_public(db, sample.obj.id)

    response = client.get(f"{API_URL}/{sample.project.id}/flights")
    assert response.status_code == status.HTTP_200_OK
    flights = response.json()
    assert len(flights) == 1
    assert len(flights[0]["data_products"]) == 1
    assert flights[0]["data_products"][0]["id"] == str(sample.obj.id)


def test_read_published_project_flights_excludes_private_data_products(
    client: TestClient, db: Session
) -> None:
    # data product with completed job but is_public left as False
    sample = SampleDataProduct(db, skip_job=True)
    create_job(
        db,
        data_product_id=sample.obj.id,
        name="upload-data-product",
        state=State.COMPLETED,
        status=Status.SUCCESS,
    )
    _publish(db, sample.project)

    response = client.get(f"{API_URL}/{sample.project.id}/flights")
    assert response.status_code == status.HTTP_200_OK
    flights = response.json()
    # Flight is returned but with no visible data products
    assert all(len(f["data_products"]) == 0 for f in flights)


def test_read_published_project_flights_unpublished_returns_404(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    create_flight(db, project_id=project.id)

    response = client.get(f"{API_URL}/{project.id}/flights")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_published_project_flights_inactive_returns_404(
    client: TestClient, db: Session
) -> None:
    project = create_project(db)
    _publish(db, project)
    _deactivate(db, project)

    response = client.get(f"{API_URL}/{project.id}/flights")
    assert response.status_code == status.HTTP_404_NOT_FOUND
