from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.team import TeamCreate, TeamUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.team import (
    create_random_team,
    random_team_description,
    random_team_name,
)
from app.tests.utils.team_member import create_random_team_member


def test_create_team(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify new team is created in database."""
    data = {"title": random_team_name(), "description": random_team_description()}
    r = client.post(
        f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers, json=data
    )
    assert 201 == r.status_code
    content = r.json()
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]
    assert "id" in content
    assert "is_owner" in content
    assert content["is_owner"]


def test_get_teams(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of teams owned by current user."""
    # create a team with current user as the owner
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team1_in = TeamCreate(
        title=random_team_name(), description=random_team_description()
    )
    team_owned_by_user = crud.team.create_with_owner(
        db=db, obj_in=team1_in, owner_id=current_user.id
    )
    # create a team with current user as a member (not owner)
    other_user = create_random_user(db=db)
    team2_in = TeamCreate(
        title=random_team_name(), description=random_team_description()
    )
    team_owned_by_other_user = crud.team.create_with_owner(
        db=db, obj_in=team2_in, owner_id=other_user.id
    )
    create_random_team_member(
        db=db, member_id=current_user.id, team_id=team_owned_by_other_user.id
    )
    r = client.get(f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers)
    assert 200 == r.status_code
    teams = r.json()
    assert type(teams) is list
    assert len(teams) > 1
    for team in teams:
        assert "title" in team
        assert "description" in team
        assert "is_owner" in team
        if str(team_owned_by_user.id) == team["id"]:
            assert team["is_owner"]
        else:
            assert team["is_owner"] is False


def test_get_team(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify team belonging to current user can be retrieved by its id."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team = create_random_team(db, owner_id=current_user.id)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers
    )
    assert 200 == r.status_code
    response_team = r.json()
    assert str(team.id) == response_team["id"]
    assert team.title == response_team["title"]
    assert team.description == response_team["description"]
    # assert str(team.owner_id) == response_team["owner_id"]


def test_get_team_not_owned_by_current_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify current user must be team member to retrieve team details."""
    different_user = create_random_user(db)
    team = create_random_team(db, owner_id=different_user.id)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers
    )
    assert 403 == r.status_code


def test_update_team(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update changes team attributes in database."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team = TeamCreate(title=random_team_name(), description=random_team_description())
    team = crud.team.create_with_owner(db, obj_in=team, owner_id=current_user.id)
    new_title = random_team_name()
    new_description = random_team_description()
    team_in = TeamUpdate(title=new_title, description=new_description)
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in.dict(),
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_team = r.json()
    assert str(team.id) == updated_team["id"]
    assert new_title == updated_team["title"]
    assert new_description == updated_team["description"]
