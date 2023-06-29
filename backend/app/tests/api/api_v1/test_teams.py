from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.team import TeamCreate, TeamUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.team import create_random_team, random_team_description, random_team_name


def test_create_team(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a new team for current user."""
    data = {"title": random_team_name(), "description": random_team_description()}

    r = client.post(f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers, json=data)
    
    assert r.status_code == 201
    content = r.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_get_teams(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Test retrieiving list of teams owned by current user."""
    current_user = get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1])
    team1_in = TeamCreate(title=random_team_name(), description=random_team_description())
    crud.team.create_with_owner(db, obj_in=team1_in, owner_id=current_user.id)
    team2_in = TeamCreate(title=random_team_name(), description=random_team_description())
    crud.team.create_with_owner(db, obj_in=team2_in, owner_id=current_user.id)

    r = client.get(f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers)

    assert r.status_code == 200
    teams = r.json()
    assert type(teams) is list
    assert len(teams) > 1
    for team in teams:
        assert "title" in team
        assert "description" in team
        assert "owner_id" in team
        assert team["owner_id"] == str(current_user.id)


def test_get_team(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Test retrieiving single team owned by current user."""
    current_user = get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1])
    team = create_random_team(db, owner_id=current_user.id)

    r = client.get(f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers)

    assert r.status_code == 200
    response_team = r.json()
    assert str(team.id) == response_team["id"]
    assert team.title == response_team["title"]
    assert team.description == response_team["description"]
    assert str(team.owner_id) == response_team["owner_id"]


def test_get_team_not_owned_by_current_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Test retrieiving single team not owned by current user."""
    current_user = get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1])
    different_user = create_random_user(db)
    team = create_random_team(db, owner_id=different_user.id)

    r = client.get(f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers)

    assert r.status_code == 401


def test_update_team(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Test updating a team owned by current user."""
    current_user = get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1])
    team = TeamCreate(title=random_team_name(), description=random_team_description())
    team = crud.team.create_with_owner(db, obj_in=team, owner_id=current_user.id)
    new_title = random_team_name()
    new_description = random_team_description()
    team_in = TeamUpdate(title=new_title, description=new_description)

    r = client.put(f"{settings.API_V1_STR}/teams/{team.id}", json=team_in.dict(), headers=normal_user_token_headers)

    assert r.status_code == 200
    updated_team = r.json()
    assert updated_team["id"] == str(team.id)
    assert updated_team["title"] == new_title
    assert updated_team["description"] == new_description
