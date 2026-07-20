from datetime import date, datetime, timezone
from typing import Any, Dict
from unittest.mock import patch

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tasks.stac_tasks import publish_stac_catalog_task
from app.tests.conftest import pytest_requires_stac
from app.schemas.data_product import DataProductCreate
from app.schemas.project import ProjectUpdate
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.role import Role
from app.schemas.team_member import TeamMemberUpdate
from app.schemas.user import UserUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.location import create_location
from app.tests.utils.project import (
    create_project,
    random_planting_date,
    random_harvest_date,
)
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.team import create_team, random_team_name, random_team_description
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user, update_regular_user_to_superuser
from app.tests.utils.utils import get_geojson_feature_collection
from app.utils.stac.STACCollectionManager import STACCollectionManager

API_URL = f"{settings.API_V1_STR}/projects"


def test_create_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert data["title"] == response_data["title"]
    assert data["description"] == response_data["description"]
    assert data["planting_date"] == response_data["planting_date"]
    assert data["harvest_date"] == response_data["harvest_date"]
    assert "location_id" in response_data
    assert response_data["is_active"] is True
    assert response_data["is_published"] is False


def test_create_project_with_team_with_team_owner_role(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db, owner_id=current_user.id)
    create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
            "team_id": team.id,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["team_id"] == str(team.id)


def test_create_project_with_team_with_team_member_role(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db)
    create_team_member(db, email=current_user.email, team_id=team.id)
    create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
            "team_id": team.id,
        }
    )
    response = client.post(API_URL, json=data)
    # User must be team owner to create project with team
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_with_team_without_team_role(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    team = create_team(db)
    create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
            "team_id": team.id,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_with_demo_user(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    project_data = {
        "title": random_team_name(),
        "description": random_team_description(),
        "planting_date": random_planting_date(),
        "harvest_date": random_harvest_date(),
        "location": get_geojson_feature_collection("polygon")["geojson"]["features"][0],
    }
    response = client.post(API_URL, json=jsonable_encoder(project_data))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_rejects_multipolygon(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    create_location(db)
    polygon_coords = get_geojson_feature_collection("polygon")["geojson"][
        "features"
    ][0]["geometry"]["coordinates"]
    multipolygon_feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [polygon_coords],
        },
    }
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "location": multipolygon_feature,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert len(detail) == 1, f"Expected single-message detail, got: {detail}"
    msg = detail[0]["msg"]
    assert "MultiPolygon" in msg
    assert "Polygon" in msg


def test_create_project_rejects_point_geometry(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    create_location(db)
    point_feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "Point", "coordinates": [-86.94, 41.44]},
    }
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "location": point_feature,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert len(detail) == 1, f"Expected single-message detail, got: {detail}"
    msg = detail[0]["msg"]
    assert "Polygon" in msg
    assert "Point" in msg


def test_create_project_date_validation(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    current_year = datetime.now().year
    location = create_location(db)
    # invalid - harvest_date before planting_date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": date(current_year, 6, 1),
            "harvest_date": date(current_year, 5, 1),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # valid - only planting_date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": date(current_year, 6, 1),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED

    # valid - only harvest_date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "harvest_date": date(current_year, 6, 1),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED

    # valid - harvest_date on planting date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": date(current_year, 6, 1),
            "harvest_date": date(current_year, 6, 1),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED

    # valid - harvest_date after planting date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": date(current_year, 6, 1),
            "harvest_date": date(current_year, 6, 2),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED

    # valid - no planting_date and no harvest_date
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "location": get_geojson_feature_collection("polygon")["geojson"][
                "features"
            ][0],
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_get_project_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert project.title == response_data["title"]
    assert project.description == response_data["description"]
    assert str(project.planting_date) == response_data["planting_date"]
    assert str(project.harvest_date) == response_data["harvest_date"]
    assert response_data["location_id"]
    assert response_data["role"] == "owner"
    # created_by should be owner's details
    assert response_data.get("created_by") == {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
    }


def test_get_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_uuid=project.id, role=Role.MANAGER
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK


def test_get_project_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, email=current_user.email, project_uuid=project.id, role=Role.VIEWER
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["role"] != "owner"
    # created_by should be owner's details
    assert response_data.get("created_by") == {
        "first_name": project_owner.first_name,
        "last_name": project_owner.last_name,
        "email": project_owner.email,
    }


def test_get_project_by_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_projects(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project1 = create_project(db, owner_id=current_user.id)
    project2 = create_project(db)
    project2_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db, obj_in=project2_member_in, project_uuid=project2.id
    )
    create_project(db)
    response = client.get(API_URL)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 2
    for project in response_data:
        assert "title" in project
        assert "description" in project
        assert "role" in project
        assert "centroid" in project
        assert "x" in project["centroid"] and "y" in project["centroid"]
        assert str(project1.id) == project["id"] or str(project2.id) == project["id"]
        if str(project1.id) == project["id"]:
            assert project["role"] == "owner"
        if str(project2.id) == project["id"]:
            assert project["role"] != "owner"


def test_get_projects_includes_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db, owner_id=current_user.id)
    project = create_project(db, owner_id=current_user.id, team_id=team.id)
    response = client.get(API_URL)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # Find the project and ensure team object is present
    matched = next((p for p in response_data if p["id"] == str(project.id)), None)
    assert matched is not None
    assert "team" in matched
    assert matched["team"] is not None
    assert matched["team"]["id"] == str(team.id)


def test_get_projects_with_flights(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project1 = create_project(db, owner_id=current_user.id)
    create_flight(db, project_id=project1.id, acquisition_date=date(2022, 6, 15))
    create_flight(db, project_id=project1.id, acquisition_date=date(2022, 2, 15))
    create_flight(db, project_id=project1.id, acquisition_date=date(2022, 10, 15))
    response = client.get(API_URL)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 1
    assert response_data[0]["id"] == str(project1.id)
    assert "most_recent_flight" in response_data[0]
    assert response_data[0]["most_recent_flight"] == str(date(2022, 10, 15))


def test_get_projects_by_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    updated_user = update_regular_user_to_superuser(db, user_id=current_user.id)

    # create three projects with only two owned by current user
    project1 = create_project(db, owner_id=current_user.id)
    project2 = create_project(db, owner_id=current_user.id)
    project3 = create_project(db)
    # request projects
    response = client.get(API_URL, params={"include_all": True})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 3
    for project in response_data:
        assert project["id"] in [str(project1.id), str(project2.id), str(project3.id)]


def test_get_projects_with_include_all_by_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    # create three projects with only two owned by current user
    project1 = create_project(db, owner_id=current_user.id)
    project2 = create_project(db, owner_id=current_user.id)
    project3 = create_project(db)
    # request projects
    response = client.get(API_URL, params={"include_all": True})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 2
    for project in response_data:
        assert project["id"] in [str(project1.id), str(project2.id)]


def test_get_projects_with_specific_data_type(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    # create three projects
    project1 = create_project(db)
    project2 = create_project(db)
    project3 = create_project(db)
    projects = [project1, project2, project3]
    # add user as project member to all three projects
    create_project_member(db, member_id=current_user.id, project_uuid=project1.id)
    create_project_member(db, member_id=current_user.id, project_uuid=project2.id)
    create_project_member(db, member_id=current_user.id, project_uuid=project3.id)
    # create flight for each project
    for project_idx, project in enumerate(projects):
        flight = create_flight(db, project_id=project.id)
        # add raster data product to first project
        if project_idx == 0:
            raster_data_product = SampleDataProduct(
                db, data_type="ortho", flight=flight, project=project
            )
        # add point cloud data product to second project
        if project_idx == 1:
            point_cloud_data_product = crud.data_product.create_with_flight(
                db,
                obj_in=DataProductCreate(
                    data_type="point_cloud",
                    filepath="null",
                    original_filename="test.las",
                ),
                flight_id=flight.id,
            )
    response = client.get(API_URL, params={"has_raster": True})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1
    assert response_data[0]["id"] == str(project1.id)


def test_update_project_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    location = create_location(db)
    assert hasattr(location, "properties")
    assert isinstance(location.properties, dict)
    assert "id" in location.properties
    project_in = jsonable_encoder(
        ProjectUpdate(
            title=random_team_name(),
            description=random_team_description(),
            planting_date=random_planting_date(),
            harvest_date=random_harvest_date(),
            location_id=location.properties["id"],
        ).model_dump()
    )
    response = client.put(f"{API_URL}/{project.id}", json=project_in)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["role"] == "owner"
    assert project_in["title"] == response_data["title"]
    assert project_in["description"] == response_data["description"]
    assert project_in["planting_date"] == response_data["planting_date"]
    assert project_in["harvest_date"] == response_data["harvest_date"]
    assert project_in["location_id"] == response_data["location_id"]


def test_update_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    # add current user to project
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_uuid=project.id
    )
    location = create_location(db)
    assert hasattr(location, "properties")
    assert isinstance(location.properties, dict)
    assert "id" in location.properties
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.properties["id"],
        }
    )
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["role"] != "owner"
    assert update_data["title"] == response_data["title"]
    assert update_data["description"] == response_data["description"]
    assert update_data["planting_date"] == response_data["planting_date"]
    assert update_data["harvest_date"] == response_data["harvest_date"]
    assert update_data["location_id"] == response_data["location_id"]


def test_update_project_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    # add current user to project
    project_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_uuid=project.id
    )
    location = create_location(db)
    assert hasattr(location, "properties")
    assert isinstance(location.properties, dict)
    assert "id" in location.properties
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.properties["id"],
        }
    )
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    location = create_location(db)
    assert hasattr(location, "properties")
    assert isinstance(location.properties, dict)
    assert "id" in location.properties
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.properties["id"],
        }
    )
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_without_team_with_a_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """
    Test adding a team to an existing project with no current team association adds
    the team members to the project members table.
    """
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    # create team and add five members in addition to owner
    team = create_team(db, owner_id=current_user.id)
    team_member_ids = []
    for i in range(0, 5):
        team_member_ids.append(create_team_member(db, team_id=team.id).member_id)
    # create project with no initial team association
    project = create_project(db, owner_id=current_user.id)
    # update project to be associated with team
    update_data = {"team_id": str(team.id)}
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    response_project = response.json()
    assert response_project["team_id"] == str(team.id)
    # confirm team members are now in project members table
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    for project_member in project_members:
        if project_member.role != Role.OWNER:
            assert project_member.member_id in team_member_ids


def test_update_project_with_new_team_replacing_old_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create two teams (current and new) and populate with five team members
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    current_team = create_team(db, owner_id=current_user.id)
    current_team_member_ids = []
    new_team = create_team(db, owner_id=current_user.id)
    new_team_member_ids = []
    for i in range(0, 5):
        current_team_member = create_team_member(db, team_id=current_team.id)
        current_team_member_ids.append(current_team_member.member_id)
        new_team_member = create_team_member(db, team_id=new_team.id)
        new_team_member_ids.append(new_team_member.member_id)
    # create new project associated with current team
    project = create_project(db, team_id=current_team.id, owner_id=current_user.id)
    # update project replacing current team with new team
    update_data = jsonable_encoder({"team_id": new_team.id})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["team_id"] == str(new_team.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert len(project_members) == 11  # ten team members plus owner
    for project_member in project_members:
        if project_member.role != Role.OWNER:
            assert (
                project_member.member_id in new_team_member_ids
                or project_member.member_id in current_team_member_ids
                or project_member.id == current_user.id
            )


def test_update_project_with_team_by_team_member_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team owned by another user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team as manager
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    updated_team_member = crud.team_member.update(
        db, db_obj=team_member, obj_in=team_member_in
    )
    assert updated_team_member.role == Role.MANAGER
    # Create project owned by current user
    project = create_project(db, owner_id=current_user.id)
    # Update project with team
    response = client.put(f"{API_URL}/{project.id}", json={"team_id": str(team.id)})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["team_id"] == str(team.id)


def test_update_project_with_team_by_team_member_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team owned by another user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team as viewer
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    assert team_member.role == Role.VIEWER
    # Create project owned by current user
    project = create_project(db, owner_id=current_user.id)
    # Update project with team
    response = client.put(f"{API_URL}/{project.id}", json={"team_id": str(team.id)})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_date_validation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # valid - harvest_date when no planting_date set
    current_year = datetime.now().year
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(
        db, owner_id=current_user.id, planting_date=None, harvest_date=None
    )
    update_data = jsonable_encoder({"harvest_date": random_harvest_date()})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # valid - harvest_date after planting_date
    project = create_project(
        db,
        owner_id=current_user.id,
        planting_date=date(current_year, 6, 1),
        harvest_date=None,
    )
    update_data = jsonable_encoder({"harvest_date": date(current_year, 6, 2)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # valid - planting_date when no harvest_date set
    project = create_project(
        db, owner_id=current_user.id, planting_date=None, harvest_date=None
    )
    update_data = jsonable_encoder({"planting_date": date(current_year, 6, 2)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # valid - update harvest date to same date as planting date
    project = create_project(
        db,
        owner_id=current_user.id,
        planting_date=date(current_year, 6, 1),
        harvest_date=None,
    )
    update_data = jsonable_encoder({"harvest_date": date(current_year, 6, 1)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # invalid - harvest_date before planting_date
    project = create_project(
        db,
        owner_id=current_user.id,
        planting_date=date(current_year, 6, 1),
        harvest_date=None,
    )
    update_data = jsonable_encoder({"harvest_date": date(current_year, 5, 1)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # invalid - harvest_date before planting_date
    project = create_project(
        db,
        owner_id=current_user.id,
        planting_date=None,
        harvest_date=date(current_year, 6, 5),
    )
    update_data = jsonable_encoder({"planting_date": date(current_year, 6, 7)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_dropping_team_from_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create team owned by user and populate with five team members
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member_ids = []
    for i in range(0, 5):
        team_member = create_team_member(db, team_id=team.id)
        team_member_ids.append(team_member.member_id)
    # create new project associated with team
    project = create_project(db, team_id=team.id, owner_id=current_user.id)
    # drop current team
    update_data = jsonable_encoder({"team_id": None})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["team_id"] is None
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert len(project_members) == 6  # number of project members should remain same
    # Verify current user is still in the project members list
    current_user_in_members = any(
        member.member_id == current_user.id for member in project_members
    )
    assert current_user_in_members


def test_update_project_with_new_team_without_belonging_to_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db)
    project = create_project(db, owner_id=current_user.id)
    update_data = jsonable_encoder({"team_id": team.id})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_project_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    response = client.delete(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("is_active", True) is False
    try:
        deactivated_at = datetime.strptime(
            response_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except Exception:
        raise
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)


def test_deactivate_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, email=current_user.email, project_uuid=project.id, role=Role.MANAGER
    )
    response = client.delete(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_project_by_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    response = client.delete(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_deactivated_project_by_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    crud.project.deactivate(db, project_id=project.id, user_id=current_user.id)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_deactivated_project_by_team_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    team = create_team(db, owner_id=owner.id)
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    create_team_member(db, email=current_user.email, team_id=team.id)
    project = create_project(db, owner_id=owner.id, team_id=team.id)
    crud.project.deactivate(db, project_id=project.id, user_id=owner.id)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_deactivated_project_by_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=owner.id)
    create_project_member(db, email=current_user.email, project_uuid=project.id)
    crud.project.deactivate(db, project_id=project.id, user_id=owner.id)
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deactivate_project_deactivates_flights_and_data_products(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight_ids = []
    data_product_ids = []
    # create three flights with one data product each for the project
    for n in range(0, 3):
        flight = create_flight(db, project_id=project.id)
        flight_ids.append(flight.id)
        data_product = SampleDataProduct(db, project=project, flight=flight)
        data_product_ids.append(data_product.obj.id)

    response = client.delete(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("is_active", True) is False
    for flight_id in flight_ids:
        deactivated_flight = crud.flight.get(db, id=flight_id)
        assert deactivated_flight is not None
        assert deactivated_flight.is_active is False
    for data_product_id in data_product_ids:
        deactivated_data_product = crud.data_product.get(db, id=data_product_id)
        assert deactivated_data_product is not None
        assert deactivated_data_product.is_active is False


@pytest_requires_stac
def test_publish_project_to_stac_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test publishing project to STAC using the task function."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app import crud

    # Create project owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(db, project=project, flight=flight2)

    # Publish project to STAC using task function
    result = publish_stac_catalog_task(str(project.id), db=db)

    # Confirm that the project is published to STAC
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert result["is_published"] is True
    assert len(result["items"]) == 2

    # Verify all items are present
    expected_ids = {str(data_product1.obj.id), str(data_product2.obj.id)}
    item_ids = {item["id"] for item in result["items"]}
    assert item_ids == expected_ids

    # Confirm that data products are now public
    data_product1_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product1.obj.id
    )
    assert data_product1_file_permission is not None
    assert data_product1_file_permission.is_public is True

    # Clean up - remove from STAC catalog
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


@pytest_requires_stac
def test_publish_project_to_stac_excludes_deactivated_data_products_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test that deactivated data products are not included when publishing to STAC using task."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app import crud

    # Create project owned by current user with one flight and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight)
    data_product2 = SampleDataProduct(db, project=project, flight=flight)

    # Deactivate one of the data products
    deactivated_data_product = crud.data_product.deactivate(
        db, data_product_id=data_product1.obj.id
    )
    assert deactivated_data_product is not None
    assert deactivated_data_product.is_active is False

    # Publish project to STAC using task function
    result = publish_stac_catalog_task(str(project.id), db=db)

    # Confirm that the project is published to STAC
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert result["is_published"] is True

    # Only one data product should be published (the active one)
    assert len(result["items"]) == 1

    # Verify only the active data product is in the response
    published_item_ids = {item["id"] for item in result["items"]}
    assert str(data_product2.obj.id) in published_item_ids
    assert str(data_product1.obj.id) not in published_item_ids

    # Clean up
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


@pytest_requires_stac
def test_generate_stac_preview_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview using the task function."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import generate_stac_preview_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app import crud

    # Create project owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(db, project=project, flight=flight2)

    # Generate preview using task function
    result = generate_stac_preview_task(str(project.id), db=db)

    # Confirm that the preview is returned
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert result["is_published"] is False

    # Verify collection is a dictionary with expected structure
    collection = result["collection"]
    assert isinstance(collection, dict)
    assert collection["id"] == str(project.id)
    assert collection["title"] == project.title
    assert collection["description"] == project.description

    # Verify items are dictionaries with expected structure
    items = result["items"]
    assert isinstance(items, list)
    assert len(items) == 2

    expected_ids = {str(data_product1.obj.id), str(data_product2.obj.id)}
    for item in items:
        assert isinstance(item, dict)
        assert "id" in item
        assert "type" in item
        assert "properties" in item
        assert item["id"] in expected_ids
        assert item["type"] == "Feature"
        assert "flight_details" in item["properties"]
        assert "data_product_details" in item["properties"]
        expected_ids.remove(item["id"])

    # Verify all expected items were found
    assert len(expected_ids) == 0

    # Confirm project is not actually published (data products remain private)
    data_product1_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product1.obj.id
    )
    assert data_product1_file_permission is not None
    assert data_product1_file_permission.is_public is False


@pytest_requires_stac
def test_publish_stac_with_scientific_metadata_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test publishing project to STAC with scientific metadata using task."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Scientific metadata
    test_doi = "10.1000/test123"
    test_citation = (
        "Smith, J., et al. (2023). Test Dataset. Journal of Test Data, 1(1), 1-10."
    )

    # Publish project to STAC with scientific metadata using task
    result = publish_stac_catalog_task(
        str(project.id), sci_doi=test_doi, sci_citation=test_citation, db=db
    )

    # Confirm that the project is published to STAC
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert result["is_published"] is True

    # Fetch the published collection to verify scientific metadata
    stac_collection_manager = STACCollectionManager(collection_id=str(project.id))
    collection = stac_collection_manager.fetch_public_collection()
    assert collection is not None

    # Verify scientific extension and metadata are present
    assert "stac_extensions" in collection
    assert (
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
        in collection["stac_extensions"]
    )
    assert collection.get("sci:doi") == test_doi
    assert collection.get("sci:citation") == test_citation

    # Clean up
    stac_collection_manager.remove_from_catalog()


@pytest_requires_stac
def test_publish_stac_with_custom_titles_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test publishing project to STAC with custom titles using task."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(db, project=project, flight=flight2)

    # Custom titles for the data products
    custom_titles = {
        str(data_product1.obj.id): "Custom Title for First Product",
        str(data_product2.obj.id): "Custom Title for Second Product",
    }

    # Publish project to STAC with custom titles using task
    result = publish_stac_catalog_task(
        str(project.id), custom_titles=custom_titles, db=db
    )

    # Confirm that the project is published to STAC
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert result["is_published"] is True
    assert len(result["items"]) == 2

    # Fetch the published items to verify custom titles
    stac_collection_manager = STACCollectionManager(collection_id=str(project.id))

    # Verify custom titles are present in published items
    item1 = stac_collection_manager.fetch_public_item(str(data_product1.obj.id))
    assert item1 is not None
    assert item1["properties"]["title"] == "Custom Title for First Product"

    item2 = stac_collection_manager.fetch_public_item(str(data_product2.obj.id))
    assert item2 is not None
    assert item2["properties"]["title"] == "Custom Title for Second Product"

    # Clean up
    stac_collection_manager.remove_from_catalog()


@pytest_requires_stac
def test_publish_stac_with_failed_items_using_task(
    db: Session, normal_user_access_token: str, monkeypatch
) -> None:
    """Test publishing project to STAC when some items fail to generate using task."""
    from app.api.deps import get_current_approved_user, get_current_user
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.data_product import SampleDataProduct
    from app.tests.utils.flight import create_flight
    from app.tests.utils.project import create_project
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)

    # Create one regular data product and one point cloud data product
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(
        db, project=project, flight=flight2, data_type="point_cloud"
    )

    # Mock pdal_to_stac.create_item to raise a ValueError for point cloud processing
    def mock_create_item(*args, **kwargs):
        raise ValueError("Unable to find bounding box")

    monkeypatch.setattr("app.utils.stac.pdal_to_stac.create_item", mock_create_item)

    # Publish project to STAC using task
    result = publish_stac_catalog_task(str(project.id), db=db)

    # Should succeed with partial publication
    assert result is not None
    assert str(result["collection_id"]) == str(project.id)
    assert (
        result["is_published"] is True
    )  # Should be published since we have one successful item
    assert len(result["items"]) == 1  # Only successful items in main items array
    assert "failed_items" in result
    assert len(result["failed_items"]) == 1  # Failed items in separate array

    # Verify the successful item
    successful_item = result["items"][0]
    assert successful_item["id"] == str(data_product1.obj.id)

    # Verify the failed item
    failed_item_dict = result["failed_items"][0]
    assert failed_item_dict["item_id"] == str(data_product2.obj.id)
    assert failed_item_dict["is_published"] is False
    assert failed_item_dict["error"]["code"] == "ITEM_GENERATION_FAILED"
    assert "Unable to find bounding box" in failed_item_dict["error"]["message"]

    # Clean up
    stac_collection_manager = STACCollectionManager(collection_id=str(project.id))
    stac_collection_manager.remove_from_catalog()


@pytest_requires_stac
def test_get_stac_cache_exists(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting cached STAC metadata when cache exists."""
    from app.tasks.stac_tasks import generate_stac_preview_task

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # First generate STAC metadata to create cache using task function
    generate_stac_preview_task(str(project.id), db=db)

    # Now test getting cached metadata
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert str(response_data["collection_id"]) == str(project.id)
    assert response_data["is_published"] is False
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == str(data_product.obj.id)


@pytest_requires_stac
def test_get_stac_cache_not_exists(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting cached STAC metadata when cache doesn't exist."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    create_flight(db, project_id=project.id)

    # Try to get cached metadata that doesn't exist
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response_data = response.json()
    assert "No cached STAC metadata found" in response_data["detail"]


@pytest_requires_stac
def test_get_stac_cache_without_permission(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting cached STAC metadata without permission."""
    # Create project owned by another user
    other_user = create_user(db)
    project = create_project(db, owner_id=other_user.id)

    # Try to get cached metadata without permission
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_stac
def test_generate_stac_preview_async(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Trigger async STAC preview generation with empty payload
    payload: Dict[str, Any] = {}
    response = client.post(
        f"{API_URL}/{project.id}/generate-stac-preview", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC preview generation started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_generate_stac_preview_async_with_scientific_metadata(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously with scientific metadata."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Scientific metadata
    doi = "10.1000/async123"
    citation = (
        "Async, Test, et al. (2023). Async STAC Dataset. Async Journal, 1(1), 1-10."
    )

    # Trigger async STAC preview generation with scientific metadata
    payload = {"sci_doi": doi, "sci_citation": citation}
    response = client.post(
        f"{API_URL}/{project.id}/generate-stac-preview", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC preview generation started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_generate_stac_preview_async_with_custom_titles(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously with custom titles."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Custom titles
    custom_titles = {str(data_product.obj.id): "Custom Async Title"}

    # Trigger async STAC preview generation with custom titles
    payload = {"custom_titles": custom_titles}
    response = client.post(
        f"{API_URL}/{project.id}/generate-stac-preview", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC preview generation started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_generate_stac_preview_async_without_permission(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously without permission."""
    # Create project owned by another user
    other_user = create_user(db)
    project = create_project(db, owner_id=other_user.id)

    # Try to generate preview without permission
    response = client.post(f"{API_URL}/{project.id}/generate-stac-preview")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_stac
def test_generate_stac_preview_async_with_empty_payload(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously with empty request body."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Empty payload (should work with defaults)
    payload: Dict[str, Any] = {}

    response = client.post(
        f"{API_URL}/{project.id}/generate-stac-preview", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC preview generation started" in response_data["message"]


@pytest_requires_stac
def test_publish_stac_async(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Trigger async STAC catalog publication with empty payload
    payload: Dict[str, Any] = {}
    response = client.put(f"{API_URL}/{project.id}/publish-stac-async", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC catalog publication started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_publish_stac_async_with_scientific_metadata(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously with scientific metadata."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Scientific metadata
    doi = "10.1000/asyncpub456"
    citation = "AsyncPub, Test, et al. (2023). Async Publication Dataset. AsyncPub Journal, 2(1), 5-20."

    # Trigger async STAC catalog publication with scientific metadata
    payload = {"sci_doi": doi, "sci_citation": citation}
    response = client.put(f"{API_URL}/{project.id}/publish-stac-async", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC catalog publication started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_publish_stac_async_with_custom_titles(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously with custom titles."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Custom titles
    custom_titles = {str(data_product.obj.id): "Custom Async Publish Title"}

    # Trigger async STAC catalog publication with custom titles
    payload = {"custom_titles": custom_titles}
    response = client.put(f"{API_URL}/{project.id}/publish-stac-async", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC catalog publication started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_publish_stac_async_without_permission(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously without permission."""
    # Create project owned by another user
    other_user = create_user(db)
    project = create_project(db, owner_id=other_user.id)

    # Try to publish without permission
    response = client.put(f"{API_URL}/{project.id}/publish-stac-async")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_stac
def test_publish_stac_async_with_empty_payload(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously with empty request body."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Empty payload (should work with defaults)
    payload: Dict[str, Any] = {}

    response = client.put(f"{API_URL}/{project.id}/publish-stac-async", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC catalog publication started" in response_data["message"]


@pytest_requires_stac
def test_stac_cache_with_failed_items_preview(
    client: TestClient, db: Session, normal_user_access_token: str, monkeypatch
) -> None:
    """Test STAC cache contains failed items in preview mode."""
    from app.tasks.stac_tasks import generate_stac_preview_task

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)

    # Create one regular data product and one point cloud data product
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(
        db, project=project, flight=flight2, data_type="point_cloud"
    )

    # Mock pdal_to_stac.create_item to raise a ValueError for point cloud processing
    def mock_create_item(*args, **kwargs):
        raise ValueError("Unable to process point cloud")

    monkeypatch.setattr("app.utils.stac.pdal_to_stac.create_item", mock_create_item)

    # Generate preview to create cache using task function
    generate_stac_preview_task(str(project.id), db=db)

    # Get cached metadata
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert str(response_data["collection_id"]) == str(project.id)
    assert response_data["is_published"] is False
    assert len(response_data["items"]) == 1  # Only successful items
    assert "failed_items" in response_data
    assert len(response_data["failed_items"]) == 1  # Failed items

    # Verify successful item
    successful_item = response_data["items"][0]
    assert successful_item["id"] == str(data_product1.obj.id)

    # Verify failed item
    failed_item = response_data["failed_items"][0]
    assert failed_item["item_id"] == str(data_product2.obj.id)
    assert failed_item["is_published"] is False
    assert failed_item["error"]["code"] == "ITEM_GENERATION_FAILED"
    assert "Unable to process point cloud" in failed_item["error"]["message"]


@pytest_requires_stac
def test_stac_cache_path_helper():
    """Test the get_stac_cache_path helper function."""
    from app.tasks.stac_tasks import get_stac_cache_path
    from uuid import uuid4
    import os

    project_id = uuid4()
    cache_path = get_stac_cache_path(project_id)

    # Verify path structure
    expected_dir = os.path.join("projects", str(project_id))
    assert expected_dir in str(cache_path)
    assert cache_path.name == "stac.json"


@pytest_requires_stac
def test_async_endpoints_with_missing_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test async endpoints with non-existent project ID."""
    from uuid import uuid4

    fake_project_id = uuid4()

    # Test generate-stac-preview with missing project
    response = client.post(f"{API_URL}/{fake_project_id}/generate-stac-preview")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test publish-stac-async with missing project
    response = client.put(f"{API_URL}/{fake_project_id}/publish-stac-async")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test stac-cache with missing project
    response = client.get(f"{API_URL}/{fake_project_id}/stac-cache")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_stac
def test_stac_cache_after_successful_publication(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that cache is created and updated after successful publication."""
    from app.tasks.stac_tasks import (
        generate_stac_preview_task,
        publish_stac_catalog_task,
    )

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Generate preview first (creates cache) using task function
    generate_stac_preview_task(str(project.id), db=db)

    # Verify cache exists and shows unpublished
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_200_OK
    cache_data = response.json()
    assert cache_data["is_published"] is False

    # Now publish the project using task function
    publish_stac_catalog_task(str(project.id), db=db)

    # Verify cache is updated to show published
    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_200_OK
    cache_data = response.json()
    assert cache_data["is_published"] is True
    assert len(cache_data["items"]) == 1
    assert cache_data["items"][0]["id"] == str(data_product.obj.id)

    # Clean up - remove from STAC catalog
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


@pytest_requires_stac
def test_generate_stac_preview_async_with_license(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test generating STAC preview asynchronously with license parameter."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # License parameter
    license_param = "MIT"

    # Trigger async STAC preview generation with license
    payload = {"license": license_param}
    response = client.post(
        f"{API_URL}/{project.id}/generate-stac-preview", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC preview generation started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_publish_stac_async_with_license(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test publishing STAC catalog asynchronously with license parameter."""
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # License parameter
    license_param = "ISC"

    # Trigger async STAC catalog publication with license
    payload = {"license": license_param}
    response = client.put(f"{API_URL}/{project.id}/publish-stac-async", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data is not None
    assert "STAC catalog publication started" in response_data["message"]
    assert "task_id" in response_data
    assert str(response_data["project_id"]) == str(project.id)


@pytest_requires_stac
def test_stac_with_license_using_task(
    db: Session, normal_user_access_token: str
) -> None:
    """Test STAC generation and publication with license using task functions."""
    from app.tasks.stac_tasks import (
        generate_stac_preview_task,
        publish_stac_catalog_task,
    )

    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Test license
    test_license = "GPL-3.0"

    # Generate preview with license using task function
    preview_result = generate_stac_preview_task(
        str(project.id), license=test_license, db=db
    )

    # Verify preview result includes correct license
    assert preview_result is not None
    assert str(preview_result["collection_id"]) == str(project.id)
    assert preview_result["is_published"] is False
    assert preview_result["collection"]["license"] == test_license

    # Publish with license using task function
    publish_result = publish_stac_catalog_task(
        str(project.id), license=test_license, db=db
    )

    # Verify publish result includes correct license
    assert publish_result is not None
    assert str(publish_result["collection_id"]) == str(project.id)
    assert publish_result["is_published"] is True
    assert publish_result["collection"]["license"] == test_license

    # Clean up - remove from STAC catalog
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


def _seed_s3_urls_after_publish(db, project, dp, raw=None):
    """Stamp s3_url on a project's data product (and optional raw data) so the
    unpublish cleanup path has something to find."""
    crud.data_product.update_s3_url(
        db,
        data_product_id=dp.obj.id,
        s3_url=f"https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/dp/{dp.obj.id}.tif",
    )
    if raw is not None:
        crud.raw_data.update_s3_url(
            db,
            raw_data_id=raw.obj.id,
            s3_url=f"https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/raw/{raw.obj.id}.zip",
        )


@pytest_requires_stac
def test_unpublish_stac_cleans_up_s3_when_configured(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """When S3 is configured, unpublishing should delete uploaded objects and clear s3_url columns."""
    from unittest.mock import patch
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.raw_data import SampleRawData

    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    raw = SampleRawData(db, project=project, flight=flight)

    publish_stac_catalog_task(str(project.id), db=db)
    _seed_s3_urls_after_publish(db, project, dp, raw)

    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=True
    ), patch(
        "app.api.api_v1.endpoints.stac.delete_s3_objects", return_value=True
    ) as mock_delete:
        response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    assert response.status_code == status.HTTP_200_OK
    assert mock_delete.call_count == 1
    deleted_keys = mock_delete.call_args[0][0]
    assert len(deleted_keys) == 2
    assert any(str(dp.obj.id) in key for key in deleted_keys)
    assert any(str(raw.obj.id) in key for key in deleted_keys)
    assert crud.data_product.get(db, id=dp.obj.id).s3_url is None
    assert crud.raw_data.get(db, id=raw.obj.id).s3_url is None


@pytest_requires_stac
def test_unpublish_stac_aborts_when_s3_delete_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """If S3 delete fails, the unpublish must abort with 503: the catalog stays
    intact, the project stays published, and s3_url columns are preserved so
    the user can retry once S3 is reachable."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    raw = SampleRawData(db, project=project, flight=flight)

    publish_stac_catalog_task(str(project.id), db=db)
    _seed_s3_urls_after_publish(db, project, dp, raw)

    seeded_dp_url = crud.data_product.get(db, id=dp.obj.id).s3_url
    seeded_raw_url = crud.raw_data.get(db, id=raw.obj.id).s3_url

    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=True
    ), patch(
        "app.api.api_v1.endpoints.stac.delete_s3_objects", return_value=False
    ) as mock_delete, patch(
        "app.api.api_v1.endpoints.stac.STACCollectionManager.remove_from_catalog"
    ) as mock_remove:
        response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert mock_delete.call_count == 1
    # Catalog removal must NOT have run — we abort first so retry works
    mock_remove.assert_not_called()
    # s3_url columns must survive so the orphaned objects remain trackable
    assert crud.data_product.get(db, id=dp.obj.id).s3_url == seeded_dp_url
    assert crud.raw_data.get(db, id=raw.obj.id).s3_url == seeded_raw_url
    # Project must still be marked published
    refreshed_project = crud.project.get(db, id=project.id)
    assert refreshed_project.is_published is True
    # Generic message — no bucket/path/AWS detail
    body = response.json()
    assert "S3" in body["detail"] or "s3" in body["detail"]
    assert "bucket" in body["detail"].lower()
    # The detail must NOT include any keys, paths, or specific error codes
    assert "NoSuchBucket" not in body["detail"]
    for url in (seeded_dp_url, seeded_raw_url):
        assert url not in body["detail"]


@pytest_requires_stac
def test_unpublish_stac_post_cleanup_state_unchanged_when_s3_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A failed unpublish must be retriable: the second attempt (with S3 working)
    should clean up successfully and complete the unpublish."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    publish_stac_catalog_task(str(project.id), db=db)
    _seed_s3_urls_after_publish(db, project, dp)

    # First attempt: S3 broken — abort, leave state intact
    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=True
    ), patch(
        "app.api.api_v1.endpoints.stac.delete_s3_objects", return_value=False
    ):
        first = client.delete(f"{API_URL}/{project.id}/delete-stac")
    assert first.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert crud.project.get(db, id=project.id).is_published is True

    # Second attempt: S3 fixed — full unpublish succeeds
    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=True
    ), patch(
        "app.api.api_v1.endpoints.stac.delete_s3_objects", return_value=True
    ):
        second = client.delete(f"{API_URL}/{project.id}/delete-stac")
    assert second.status_code == status.HTTP_200_OK
    assert crud.project.get(db, id=project.id).is_published is False
    assert crud.data_product.get(db, id=dp.obj.id).s3_url is None


@pytest_requires_stac
def test_unpublish_stac_skips_s3_cleanup_when_not_configured(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """When S3 is not configured, unpublish must not attempt S3 deletion
    and must leave any persisted s3_url values untouched."""
    from unittest.mock import patch
    from app.tasks.stac_tasks import publish_stac_catalog_task
    from app.tests.utils.raw_data import SampleRawData

    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    raw = SampleRawData(db, project=project, flight=flight)

    publish_stac_catalog_task(str(project.id), db=db)
    _seed_s3_urls_after_publish(db, project, dp, raw)

    seeded_dp_url = crud.data_product.get(db, id=dp.obj.id).s3_url
    seeded_raw_url = crud.raw_data.get(db, id=raw.obj.id).s3_url
    assert seeded_dp_url is not None
    assert seeded_raw_url is not None

    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=False
    ), patch(
        "app.api.api_v1.endpoints.stac.delete_s3_objects"
    ) as mock_delete:
        response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    assert response.status_code == status.HTTP_200_OK
    mock_delete.assert_not_called()
    assert crud.data_product.get(db, id=dp.obj.id).s3_url == seeded_dp_url
    assert crud.raw_data.get(db, id=raw.obj.id).s3_url == seeded_raw_url


@pytest_requires_stac
def test_unpublish_stac_deletes_local_stac_cache(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """The local stac.json cache should be removed so re-publish doesn't see stale URLs."""
    from unittest.mock import patch
    from app.tasks.stac_tasks import get_stac_cache_path, publish_stac_catalog_task

    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight)
    publish_stac_catalog_task(str(project.id), db=db)

    cache_path = get_stac_cache_path(project.id)
    assert cache_path.exists()

    with patch("app.api.api_v1.endpoints.stac.is_s3_configured", return_value=False):
        response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    assert response.status_code == status.HTTP_200_OK
    assert not cache_path.exists()


@pytest_requires_stac
def test_unpublish_stac_aborts_when_s3_cleanup_raises(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Any unexpected exception from S3 cleanup must abort the unpublish with a
    503 — the project stays published so the user can retry."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    publish_stac_catalog_task(str(project.id), db=db)
    _seed_s3_urls_after_publish(db, project, dp)

    with patch(
        "app.api.api_v1.endpoints.stac.is_s3_configured", return_value=True
    ), patch(
        "app.api.api_v1.endpoints.stac._cleanup_s3_for_project",
        side_effect=RuntimeError("s3 down"),
    ), patch(
        "app.api.api_v1.endpoints.stac.STACCollectionManager.remove_from_catalog"
    ) as mock_remove:
        response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    mock_remove.assert_not_called()
    refreshed_project = crud.project.get(db, id=project.id)
    assert refreshed_project.is_published is True


@pytest_requires_stac
def test_publish_does_not_call_s3_when_not_configured(
    db: Session, normal_user_access_token: str
) -> None:
    """Publish must skip the S3 upload helper when S3 is not configured."""
    from unittest.mock import patch
    from app.tasks.stac_tasks import publish_stac_catalog_task

    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight)

    with patch(
        "app.tasks.stac_tasks.is_s3_configured", return_value=False
    ), patch(
        "app.tasks.stac_tasks._upload_to_s3_and_rewrite_hrefs"
    ) as mock_upload:
        publish_stac_catalog_task(str(project.id), db=db)

    mock_upload.assert_not_called()

    # Clean up - remove from STAC catalog
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


@pytest_requires_stac
def test_publish_calls_s3_upload_helper_when_configured(
    db: Session, normal_user_access_token: str
) -> None:
    """Publish must invoke the S3 upload helper when S3 is configured."""
    from unittest.mock import patch
    from app.tasks.stac_tasks import publish_stac_catalog_task

    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight)

    with patch(
        "app.tasks.stac_tasks.is_s3_configured", return_value=True
    ), patch(
        "app.tasks.stac_tasks._upload_to_s3_and_rewrite_hrefs", return_value=[]
    ) as mock_upload:
        publish_stac_catalog_task(str(project.id), db=db)

    mock_upload.assert_called_once()

    # Clean up - remove from STAC catalog
    from app.utils.stac.STACCollectionManager import STACCollectionManager

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()


@pytest_requires_stac
def test_publish_writes_s3_hrefs_into_stac_cache(
    client: TestClient, db: Session, normal_user_access_token: str, monkeypatch
) -> None:
    """End-to-end: when S3 is configured, the cached stac.json served via /stac-cache
    contains S3 asset hrefs and the data product row has its s3_url persisted.
    Mocks only at the upload boundary so the real rewrite helper runs."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)

    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", "us-east-1")

    fake_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/file.tif"
    with patch(
        "app.tasks.stac_tasks.is_s3_configured", return_value=True
    ), patch(
        "app.tasks.stac_tasks.upload_file_to_s3", return_value=fake_url
    ):
        publish_stac_catalog_task(str(project.id), db=db)

    response = client.get(f"{API_URL}/{project.id}/stac-cache")
    assert response.status_code == status.HTTP_200_OK
    cache_data = response.json()
    asset_hrefs = [
        asset["href"]
        for item_dict in cache_data.get("items", [])
        for asset in item_dict.get("assets", {}).values()
        if isinstance(asset, dict) and "href" in asset
    ]
    assert fake_url in asset_hrefs, (
        f"Expected S3 URL {fake_url} in cached asset hrefs, got: {asset_hrefs}"
    )

    refreshed_dp = crud.data_product.get(db, id=dp.obj.id)
    assert refreshed_dp.s3_url == fake_url

    scm = STACCollectionManager(collection_id=str(project.id))
    scm.remove_from_catalog()
