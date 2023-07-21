from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.project import ProjectUpdate
from app.schemas.project_member import ProjectMemberCreate
from app.tests.utils.location import create_random_location
from app.tests.utils.project import (
    create_random_project,
    random_planting_date,
    random_harvest_date,
)
from app.tests.utils.team import random_team_name, random_team_description


def test_create_project(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Verify new project is created in database."""
    location = create_random_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.id,
        }
    )
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert 201 == r.status_code
    content = r.json()
    assert "id" in content
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]
    assert data["planting_date"] == content["planting_date"]
    assert data["harvest_date"] == content["harvest_date"]


def test_get_projects(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of projects the current user belongs to."""
    # create two projects with current user as a member
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    # create project with current user as owner
    project1 = create_random_project(db, owner_id=current_user.id)
    # create project with a different user as owner
    project2 = create_random_project(db)
    # add current user as member to project2
    project2_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=project2.id
    )
    crud.project_member.create_with_project(
        db, obj_in=project2_member_in, member_id=current_user.id, project_id=project2.id
    )
    # create project that current user does not belong to
    create_random_project(db)
    # request list of projects the current user belongs to
    r = client.get(
        f"{settings.API_V1_STR}/projects/", headers=normal_user_token_headers
    )
    assert 200 == r.status_code
    projects = r.json()
    assert type(projects) is list
    assert len(projects) == 2
    for project in projects:
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


def test_get_project_owned_by_current_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of project the current user owns."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project = jsonable_encoder(create_random_project(db, owner_id=current_user.id))
    r = client.get(
        f"{settings.API_V1_STR}/projects/" + project["id"],
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    response_project = r.json()
    assert project["id"] == response_project["id"]
    assert project["title"] == response_project["title"]
    assert project["description"] == response_project["description"]
    assert project["planting_date"] == response_project["planting_date"]
    assert project["harvest_date"] == response_project["harvest_date"]
    assert project["location_id"] == response_project["location_id"]
    assert "is_owner" in response_project
    assert response_project["is_owner"] is True


def test_get_project_current_user_is_member_of(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of project the current user is a member of but doesn't own."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project = create_random_project(db)
    # add current user to project
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=project.id
    )
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, member_id=current_user.id, project_id=project.id
    )
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    response_project = r.json()
    assert str(project.id) == response_project["id"]
    assert "is_owner" in response_project
    assert response_project["is_owner"] is False


def test_get_project_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to retrieve project the current user is not a member of."""
    project = create_random_project(db)
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code


def test_update_project_owned_by_current_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update by project owner changes team attributes in database."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project = create_random_project(db, owner_id=current_user.id)
    project_in = jsonable_encoder(
        ProjectUpdate(
            title=random_team_name(),
            description=random_team_description(),
            planting_date=random_planting_date(),
            harvest_date=random_harvest_date(),
            location_id=create_random_location(db).id,
        ).dict()
    )
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}",
        json=project_in,
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_project = r.json()
    assert str(project.id) == updated_project["id"]
    assert updated_project["is_owner"] is True
    assert project_in["title"] == updated_project["title"]
    assert project_in["description"] == updated_project["description"]
    assert project_in["planting_date"] == updated_project["planting_date"]
    assert project_in["harvest_date"] == updated_project["harvest_date"]
    assert project_in["location_id"] == updated_project["location_id"]


def test_update_project_current_user_is_member_of(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update of project the current user is a member of but doesn't own."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project = create_random_project(db)
    # add current user to project
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=project.id
    )
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, member_id=current_user.id, project_id=project.id
    )
    project_in = jsonable_encoder(
        ProjectUpdate(
            title=random_team_name(),
            description=random_team_description(),
            planting_date=random_planting_date(),
            harvest_date=random_harvest_date(),
            location_id=create_random_location(db).id,
        ).dict()
    )
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}",
        json=project_in,
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_project = r.json()
    assert str(project.id) == updated_project["id"]
    assert project_in["title"] == updated_project["title"]
    assert project_in["description"] == updated_project["description"]
    assert project_in["planting_date"] == updated_project["planting_date"]
    assert project_in["harvest_date"] == updated_project["harvest_date"]
    assert project_in["location_id"] == updated_project["location_id"]


def test_update_project_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to update project the current user is not a member of."""
    project = create_random_project(db)
    project_in = ProjectUpdate(
        title=random_team_name(),
        description=random_team_description(),
        planting_date=random_planting_date(),
        harvest_date=random_harvest_date(),
        location_id=create_random_location(db).id,
    )
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}",
        json=jsonable_encoder(project_in.dict()),
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code
