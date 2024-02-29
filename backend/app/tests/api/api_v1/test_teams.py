from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.team import TeamUpdate
from app.schemas.team_member import TeamMemberCreate
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.team import (
    create_team,
    random_team_description,
    random_team_name,
)
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_create_team(client: TestClient, normal_user_access_token: str) -> None:
    """Verify new team is created in database."""
    data = {"title": random_team_name(), "description": random_team_description()}
    response = client.post(f"{settings.API_V1_STR}/teams", json=data)
    response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "id" in content
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]


def test_create_team_with_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    data = {
        "title": random_team_name(),
        "description": random_team_description(),
        "project": str(project.id),
    }
    response = client.post(f"{settings.API_V1_STR}/teams", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    project_in_db = crud.project.get(db, id=project.id)
    team = response.json()
    assert str(project_in_db.team_id) == team["id"]
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id
    )
    assert len(project_members) == 1
    assert current_user.id == project_members[0].member_id


def test_create_team_with_project_already_assigned_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    existing_team = create_team(db, project=str(project.id))
    data = {
        "title": random_team_name(),
        "description": random_team_description(),
        "project": str(project.id),
    }
    response = client.post(f"{settings.API_V1_STR}/teams", json=data)
    project_in_db = crud.project.get(db, id=project.id)
    assert response.status_code == status.HTTP_201_CREATED
    team = response.json()
    assert project_in_db.team_id == existing_team.id


def test_create_team_with_project_by_project_manager(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    # add current user as project member with manager role
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    data = {
        "title": random_team_name(),
        "description": random_team_description(),
        "project": str(project.id),
    }
    response = client.post(f"{settings.API_V1_STR}/teams", json=data)
    project_in_db = crud.project.get(db, id=project.id)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert str(project_in_db.team_id) == response_data["id"]


def test_get_teams(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of teams the current user belongs to."""
    # create two teams with current user as a member
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    # create team with current user as owner
    team1 = create_team(db, owner_id=current_user.id)
    # create team with a different user as owner
    team2 = create_team(db)
    # add current user as member to team2
    team2_member_in = TeamMemberCreate(email=current_user.email)
    crud.team_member.create_with_team(db, obj_in=team2_member_in, team_id=team2.id)
    # create team that current user does not belong to
    create_team(db)
    # request list of teams the current user belongs to
    r = client.get(f"{settings.API_V1_STR}/teams")
    assert 200 == r.status_code
    teams = r.json()
    assert type(teams) is list
    assert len(teams) == 2
    for team in teams:
        assert "title" in team
        assert "description" in team
        assert "is_owner" in team
        assert str(team1.id) == team["id"] or str(team2.id) == team["id"]
        if str(team1.id) == team["id"]:
            assert team["is_owner"] is True
        if str(team2.id) == team["id"]:
            assert team["is_owner"] is False


def test_get_team_owned_by_current_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of team the current user owns."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
    )
    assert 200 == r.status_code
    response_team = r.json()
    assert str(team.id) == response_team["id"]
    assert team.title == response_team["title"]
    assert team.description == response_team["description"]
    assert "is_owner" in response_team
    assert response_team["is_owner"] is True


def test_get_team_current_user_is_member_of(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of team the current user is a member of but doesn't own."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db)
    # add current user to team
    team_member_in = TeamMemberCreate(email=current_user.email)
    crud.team_member.create_with_team(db, obj_in=team_member_in, team_id=team.id)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
    )
    assert 200 == r.status_code
    response_team = r.json()
    assert str(team.id) == response_team["id"]
    assert "is_owner" in response_team
    assert response_team["is_owner"] is False


def test_get_team_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to retrieve team the current user is not a member of."""
    team = create_team(db)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_update_team_owned_by_current_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify update by team owner changes team attributes in database."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    team_in = jsonable_encoder(
        TeamUpdate(
            title=random_team_name(),
            description=random_team_description(),
        ).model_dump()
    )
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in,
    )
    assert 200 == r.status_code
    updated_team = r.json()
    assert str(team.id) == updated_team["id"]
    assert updated_team["is_owner"] is True
    assert team_in["title"] == updated_team["title"]
    assert team_in["description"] == updated_team["description"]


def test_update_team_current_user_is_member_of_but_doesnt_own(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to update team the current user is a member of but doesn't own."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db)
    # add current user to team
    team_member_in = TeamMemberCreate(email=current_user.email)
    crud.team_member.create_with_team(db, obj_in=team_member_in, team_id=team.id)
    team_in = jsonable_encoder(
        TeamUpdate(
            title=random_team_name(),
            description=random_team_description(),
        ).model_dump()
    )
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_team_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to update project the current user is not a member of."""
    team = create_team(db)
    team_in = TeamUpdate(
        title=random_team_name(),
        description=random_team_description(),
    )
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in.model_dump(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_team_by_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    response = client.delete(f"{settings.API_V1_STR}/teams/{team.id}")
    assert response.status_code == 200
    team_in_db = crud.team.get(db, id=team.id)
    assert team_in_db is None


def test_remove_team_by_nonowner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # current user is not owner and not team member
    other_user = create_user(db)
    team = create_team(db, owner_id=other_user.id)
    response = client.delete(f"{settings.API_V1_STR}/teams/{team.id}")
    team_in_db = crud.team.get(db, id=team.id)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert team_in_db
    # current user is not owner but is a team member
    create_team_member(db, team_id=team.id, email=current_user.email)
    response = client.delete(f"{settings.API_V1_STR}/teams/{team.id}")
    team_in_db = crud.team.get(db, id=team.id)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert team_in_db


def test_remove_team_with_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create team owned by current test user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    # add five team members
    for i in range(0, 5):
        create_team_member(db, team_id=team.id)
    # create project associated with team - team members added to project members table
    project = create_project(db, team_id=team.id, owner_id=current_user.id)
    # get list of project members (should include owner plus five team members, 6)
    project_members_before_team_deleted = (
        crud.project_member.get_list_of_project_members(db, project_id=project.id)
    )
    # delete the team
    response = client.delete(f"{settings.API_V1_STR}/teams/{team.id}")
    assert response.status_code == 200
    # confirm team has been removed
    team_in_db = crud.team.get(db, id=team.id)
    assert team_in_db is None
    # get list of project members (should still be 6 members)
    project_members_after_team_deleted = (
        crud.project_member.get_list_of_project_members(db, project_id=project.id)
    )
    project_after_team_deleted = crud.project.get(db, id=project.id)
    assert len(project_members_before_team_deleted) == 6
    assert len(project_members_after_team_deleted) == 6
    # verify team_id is now null in project record
    project_after_team_deleted = crud.project.get(db, id=project.id)
    assert project_after_team_deleted.team_id is None
