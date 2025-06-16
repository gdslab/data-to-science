from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.data_product import DataProductCreate
from app.schemas.project import ProjectUpdate
from app.schemas.project_like import ProjectLikeCreate
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.role import Role
from app.schemas.stac import STACReport
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
from app.tests.utils.test_stac import (
    stac_collection_published,
    stac_collection_unpublished,
)
from app.tests.utils.STACCollectionHelper import STACCollectionHelper
from app.tests.utils.team import create_team, random_team_name, random_team_description
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user, update_regular_user_to_superuser
from app.tests.utils.utils import get_geojson_feature_collection
from app.utils.STACCollectionManager import STACCollectionManager

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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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


def test_get_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role=Role.MANAGER
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK


def test_get_project_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role=Role.VIEWER
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["role"] != "owner"


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
        db, obj_in=project2_member_in, project_id=project2.id
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
    create_project_member(db, member_id=current_user.id, project_id=project1.id)
    create_project_member(db, member_id=current_user.id, project_id=project2.id)
    create_project_member(db, member_id=current_user.id, project_id=project3.id)
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
        db, obj_in=project_member_in, project_id=project.id
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
        db, obj_in=project_member_in, project_id=project.id
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
        db, project_id=project.id
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
        db, project_id=project.id
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # invalid - harvest_date before planting_date
    project = create_project(
        db,
        owner_id=current_user.id,
        planting_date=None,
        harvest_date=date(current_year, 6, 5),
    )
    update_data = jsonable_encoder({"planting_date": date(current_year, 6, 7)})
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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
        db, project_id=project.id
    )
    assert len(project_members) == 6  # number of project members should remain same
    assert project_members[0].member_id == current_user.id


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
        db, email=current_user.email, project_id=project.id, role=Role.MANAGER
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
    create_project_member(db, email=current_user.email, project_id=project.id)
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


def test_publish_project_to_stac(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight1)
    data_product2 = SampleDataProduct(db, project=project, flight=flight2)

    # Publish project to STAC
    response = client.put(f"{API_URL}/{project.id}/publish-stac")

    # Confirm that the project is published to STAC
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    # Check that the response is a STACReport
    assert STACReport(**response_data)
    response_data = STACReport(**response_data)
    assert response_data.collection_id == project.id
    assert response_data.is_published is True
    assert response_data.collection_url is not None
    assert len(response_data.items) == 2
    # Get expected data product IDs
    expected_ids = {str(data_product1.obj.id), str(data_product2.obj.id)}

    # Verify all items are present and published
    for item in response_data.items:
        assert str(item.item_id) in expected_ids
        assert item.is_published is True
        # Remove the ID from the set to ensure we don't have duplicates
        expected_ids.remove(str(item.item_id))

    # Verify we've seen all expected IDs
    assert len(expected_ids) == 0

    # Confirm that data product1 is now public
    data_product1_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product1.obj.id
    )
    assert data_product1_file_permission is not None
    assert data_product1_file_permission.is_public is True

    # Confirm that data product2 is now public
    data_product2_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product2.obj.id
    )
    assert data_product2_file_permission is not None
    assert data_product2_file_permission.is_public is True


def test_publish_project_to_stac_excludes_deactivated_data_products(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that deactivated data products are not included when publishing to STAC."""
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

    # Publish project to STAC
    response = client.put(f"{API_URL}/{project.id}/publish-stac")

    # Confirm that the project is published to STAC
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None

    # Check that the response is a STACReport
    assert STACReport(**response_data)
    response_data = STACReport(**response_data)
    assert response_data.collection_id == project.id
    assert response_data.is_published is True
    assert response_data.collection_url is not None

    # Only one data product should be published (the active one)
    assert len(response_data.items) == 1

    # Verify only the active data product is in the response
    published_item = response_data.items[0]
    assert str(published_item.item_id) == str(data_product2.obj.id)
    assert published_item.is_published is True

    # Confirm that the deactivated data product ID is not in the response
    published_item_ids = {str(item.item_id) for item in response_data.items}
    assert str(data_product1.obj.id) not in published_item_ids

    # Confirm that only data product2 is now public
    data_product2_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product2.obj.id
    )
    assert data_product2_file_permission is not None
    assert data_product2_file_permission.is_public is True

    # Confirm that the deactivated data product1 remains private
    data_product1_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product1.obj.id
    )
    assert data_product1_file_permission is not None
    assert data_product1_file_permission.is_public is False


def test_update_project_on_stac(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    stac_collection_published: STACCollectionHelper,
) -> None:
    # Create project owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Publish a project to STAC and get the project id (e.g. collection id)
    project_id = stac_collection_published.collection_id
    assert project_id

    # Add current user as a project member with the owner role
    create_project_member(
        db, role=Role.OWNER, email=current_user.email, project_id=UUID(project_id)
    )

    # Get first data product from project
    data_product = stac_collection_published.data_product1
    original_data_type = data_product.data_type

    # Update the data type for the data product
    new_data_type = "new_data_type"
    assert original_data_type != new_data_type
    updated_data_product = crud.data_product.update_data_type(
        db,
        data_product_id=data_product.id,
        new_data_type=new_data_type,
    )
    assert updated_data_product is not None
    assert updated_data_product.data_type == new_data_type

    # Update the project on STAC
    response = client.put(f"{API_URL}/{project_id}/publish-stac")

    # Confirm that the project is updated on STAC
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert STACReport(**response_data)
    response_data = STACReport(**response_data)
    assert str(response_data.collection_id) == project_id
    assert response_data.is_published is True
    assert response_data.collection_url is not None
    assert len(response_data.items) == 2
    # Get expected data product IDs
    expected_ids = {
        str(stac_collection_published.data_product1.id),
        str(stac_collection_published.data_product2.id),
    }

    # Verify all items are present and published
    for item in response_data.items:
        assert str(item.item_id) in expected_ids
        assert item.is_published is True
        # Remove the ID from the set to ensure we don't have duplicates
        expected_ids.remove(str(item.item_id))

    # Fetch the data product STAC Item from STAC API
    stac_collection_manager = STACCollectionManager(collection_id=project_id)
    stac_item = stac_collection_manager.fetch_public_item(str(data_product.id))
    assert stac_item is not None
    # Check that the data type has been updated
    assert stac_item["properties"]["data_product_details"]["data_type"] == new_data_type


def test_remove_project_from_stac(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    stac_collection_published: STACCollectionHelper,
) -> None:
    # Create project owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Publish a project to STAC and get the project id (e.g. collection id)
    project_id = stac_collection_published.collection_id
    assert project_id
    # Add current user as a project member with the owner role
    create_project_member(
        db, role=Role.OWNER, email=current_user.email, project_id=UUID(project_id)
    )

    # Remove the project from STAC
    response = client.delete(f"{API_URL}/{project_id}/delete-stac")

    # Confirm that the project is removed from STAC
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert response_data.get("id") == str(project_id)
    assert response_data.get("is_published", True) is False

    # Fetch the collection from STAC API and confirm that it is not published
    stac_collection_manager = STACCollectionManager(collection_id=project_id)
    stac_collection = stac_collection_manager.fetch_public_collection()
    assert stac_collection is None

    # Get data products
    data_product1 = stac_collection_published.data_product1
    data_product2 = stac_collection_published.data_product2

    # Confirm that data product1 is now private
    data_product1_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product1.id
    )
    assert data_product1_file_permission is not None
    assert data_product1_file_permission.is_public is False

    # Confirm that data product2 is now private
    data_product2_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product2.id
    )
    assert data_product2_file_permission is not None
    assert data_product2_file_permission.is_public is False


def test_publish_project_to_stac_without_project_member_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project not owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight1)
    SampleDataProduct(db, project=project, flight=flight2)

    # Add current user as a project member with the manager role
    create_project_member(
        db, role=Role.MANAGER, email=current_user.email, project_id=project.id
    )

    # Publish project to STAC
    response = client.put(f"{API_URL}/{project.id}/publish-stac")

    # Confirm that the project is not published to STAC
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_on_stac_without_project_member_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project not owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight1)
    SampleDataProduct(db, project=project, flight=flight2)

    # Add current user as a project member with the manager role
    create_project_member(
        db, role=Role.MANAGER, email=current_user.email, project_id=project.id
    )

    # Publish project to STAC
    response = client.put(f"{API_URL}/{project.id}/publish-stac")

    # Confirm that the project is not published to STAC
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_project_from_stac_without_project_member_owner_role(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    # Create project not owned by current user with two flights and two data products
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight1)
    SampleDataProduct(db, project=project, flight=flight2)

    # Add current user as a project member with the manager role
    create_project_member(
        db, role=Role.MANAGER, email=current_user.email, project_id=project.id
    )

    # Remove project from STAC
    response = client.delete(f"{API_URL}/{project.id}/delete-stac")

    # Confirm that the project is not published to STAC
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_like(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    response = client.post(f"{API_URL}/{project.id}/like")
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data.get("message") == "Project bookmarked"


def test_create_project_like_by_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    response = client.post(f"{API_URL}/{project.id}/like")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_project_like(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    # Create project like
    project_like_in = ProjectLikeCreate(
        project_id=project.id,
        user_id=current_user.id,
    )
    project_like_in_db = crud.project_like.create(db, obj_in=project_like_in)
    assert crud.project_like.get(db, id=project_like_in_db.id) is not None
    # Delete project like
    response = client.delete(f"{API_URL}/{project.id}/like")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("message") == "Project unbookmarked"
    assert crud.project_like.get(db, id=project_like_in_db.id) is None


def test_delete_project_like_by_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    response = client.post(f"{API_URL}/{project.id}/like")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deactivate_project_when_published(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    # Set project as published
    crud.project.update_project_visibility(db, project_id=project.id, is_public=True)
    response = client.delete(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        response.json()["detail"]
        == "Cannot deactivate project when it is published in a STAC catalog"
    )
