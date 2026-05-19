from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project as ProjectModel
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

    _unpublished_active = create_project(db)  # noqa: F841 — intentionally not published

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
