from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.team import TeamUpdate
from app.schemas.team_member import TeamMemberCreate
from app.tests.utils.team import (
    create_random_team,
    random_team_description,
    random_team_name,
)


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
    assert "id" in content
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]


def test_get_teams(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of teams the current user belongs to."""
    # create two teams with current user as a member
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    # create team with current user as owner
    team1 = create_random_team(db, owner_id=current_user.id)
    # create team with a different user as owner
    team2 = create_random_team(db)
    # add current user as member to team2
    team2_member_in = TeamMemberCreate(member_id=current_user.id, team_id=team2.id)
    crud.team_member.create_with_team(
        db, obj_in=team2_member_in, member_id=current_user.id, team_id=team2.id
    )
    # create team that current user does not belong to
    create_random_team(db)
    # request list of teams the current user belongs to
    r = client.get(f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers)
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
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of team the current user owns."""
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
    assert "is_owner" in response_team
    assert response_team["is_owner"] is True


def test_get_team_current_user_is_member_of(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of team the current user is a member of but doesn't own."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team = create_random_team(db)
    # add current user to team
    team_member_in = TeamMemberCreate(member_id=current_user.id, team_id=team.id)
    crud.team_member.create_with_team(
        db, obj_in=team_member_in, member_id=current_user.id, team_id=team.id
    )
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers
    )
    assert 200 == r.status_code
    response_team = r.json()
    assert str(team.id) == response_team["id"]
    assert "is_owner" in response_team
    assert response_team["is_owner"] is False


def test_get_team_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to retrieve team the current user is not a member of."""
    team = create_random_team(db)
    r = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code


def test_update_team_owned_by_current_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update by team owner changes team attributes in database."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team = create_random_team(db, owner_id=current_user.id)
    team_in = jsonable_encoder(
        TeamUpdate(
            title=random_team_name(),
            description=random_team_description(),
        ).dict()
    )
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in,
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_team = r.json()
    assert str(team.id) == updated_team["id"]
    assert updated_team["is_owner"] is True
    assert team_in["title"] == updated_team["title"]
    assert team_in["description"] == updated_team["description"]


def test_update_team_current_user_is_member_of(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update of team the current user is a member of but doesn't own."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    team = create_random_team(db)
    # add current user to team
    team_member_in = TeamMemberCreate(member_id=current_user.id, team_id=team.id)
    crud.team_member.create_with_team(
        db, obj_in=team_member_in, member_id=current_user.id, team_id=team.id
    )
    team_in = jsonable_encoder(
        TeamUpdate(
            title=random_team_name(),
            description=random_team_description(),
        ).dict()
    )
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in,
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_team = r.json()
    assert str(team.id) == updated_team["id"]
    assert updated_team["is_owner"] is False
    assert team_in["title"] == updated_team["title"]
    assert team_in["description"] == updated_team["description"]


def test_update_team_current_user_does_not_belong_to(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to update project the current user is not a member of."""
    team = create_random_team(db)
    team_in = TeamUpdate(
        title=random_team_name(),
        description=random_team_description(),
    )
    r = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        json=team_in.dict(),
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code
