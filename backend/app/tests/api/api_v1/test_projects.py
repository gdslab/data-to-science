from datetime import datetime

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.project import ProjectUpdate
from app.schemas.project_member import ProjectMemberCreate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.location import create_location
from app.tests.utils.project import (
    create_project,
    random_planting_date,
    random_harvest_date,
)
from app.tests.utils.project_member import create_project_member
from app.tests.utils.team import create_team, random_team_name, random_team_description
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


API_URL = f"{settings.API_V1_STR}/projects"


def test_create_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    location = create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.id,
        }
    )
    response = client.post(API_URL, json=data)
    response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert data["title"] == response_data["title"]
    assert data["description"] == response_data["description"]
    assert data["planting_date"] == response_data["planting_date"]
    assert data["harvest_date"] == response_data["harvest_date"]


def test_create_project_with_team_with_team_owner_role(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db, owner_id=current_user.id)
    location = create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.id,
            "team_id": team.id,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["team_id"] == str(team.id)


def test_create_project_with_team_without_team_owner_role(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    team = create_team(db)
    location = create_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.id,
            "team_id": team.id,
        }
    )
    response = client.post(API_URL, json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


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
    assert str(project.location_id) == response_data["location_id"]
    assert response_data["is_owner"] is True


def test_get_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="manager"
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK


def test_get_project_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="viewer"
    )
    response = client.get(f"{API_URL}/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["is_owner"] is False


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
        assert "planting_date" in project
        assert "harvest_date" in project
        assert "location_id" in project
        assert "is_owner" in project
        assert str(project1.id) == project["id"] or str(project2.id) == project["id"]
        if str(project1.id) == project["id"]:
            assert project["is_owner"] is True
        if str(project2.id) == project["id"]:
            assert project["is_owner"] is False


def test_update_project_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    project_in = jsonable_encoder(
        ProjectUpdate(
            title=random_team_name(),
            description=random_team_description(),
            planting_date=random_planting_date(),
            harvest_date=random_harvest_date(),
            location_id=create_location(db).id,
        ).model_dump()
    )
    response = client.put(f"{API_URL}/{project.id}", json=project_in)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["is_owner"] is True
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="manager")
    proj_mem = crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": create_location(db).id,
        }
    )
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(project.id) == response_data["id"]
    assert response_data["is_owner"] is False
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
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": create_location(db).id,
        }
    )
    response = client.put(f"{API_URL}/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    update_data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": create_location(db).id,
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
        if project_member.role != "owner":
            assert project_member.member_id in team_member_ids


def test_update_project_with_new_team_replacing_old_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create two teams (current and new) and populate with five team members
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    current_team = create_team(db, owner_id=current_user.id)
    new_team = create_team(db, owner_id=current_user.id)
    new_team_member_ids = []
    for i in range(0, 5):
        create_team_member(db, team_id=current_team.id)
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
    for project_member in project_members:
        if project_member.role != "owner":
            assert project_member.member_id in new_team_member_ids


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
    assert len(project_members) == 1
    assert project_members[0].member_id == current_user.id


def test_update_project_with_new_team_without_team_owner_role(
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


def test_deactivate_project_owner_role(
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
            response_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
        )
    except Exception:
        raise
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.utcnow()


def test_deactivate_project_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="readwrite"
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
    crud.project.deactivate(db, project_id=project.id)
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
    crud.project.deactivate(db, project_id=project.id)
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
    crud.project.deactivate(db, project_id=project.id)
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
        assert deactivated_flight.is_active is False
    for data_product_id in data_product_ids:
        deactivated_data_product = crud.data_product.get(db, id=data_product_id)
        assert deactivated_data_product.is_active is False
