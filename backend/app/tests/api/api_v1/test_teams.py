from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.team import TeamUpdate
from app.schemas.team_member import TeamMemberCreate
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
    r = client.post(f"{settings.API_V1_STR}/teams", json=data)
    assert 201 == r.status_code
    content = r.json()
    assert "id" in content
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]


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
    assert 404 == r.status_code


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
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in,
    )
    assert 404 == r.status_code


def test_update_team_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to update project the current user is not a member of."""
    team = create_team(db)
    team_in = TeamUpdate(
        title=random_team_name(),
        description=random_team_description(),
    )
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in.model_dump(),
    )
    assert 404 == r.status_code


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
    assert response.status_code == 404
    assert team_in_db
    # current user is not owner but is a team member
    create_team_member(db, team_id=team.id, email=current_user.email)
    response = client.delete(f"{settings.API_V1_STR}/teams{team.id}")
    team_in_db = crud.team.get(db, id=team.id)
    assert response.status_code == 404
    assert team_in_db
