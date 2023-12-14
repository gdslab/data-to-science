from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_add_new_team_member_by_team_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify team owner can add a new member to the team."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    new_member = create_user(db)
    data = {"email": new_member.email}
    r = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/members", json=jsonable_encoder(data)
    )
    assert 201 == r.status_code
    response_data = r.json()
    new_member.id == response_data["member_id"]
    team.id == response_data["team_id"]


def test_add_new_team_member_by_regular_team_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to add new team member by another regular team member."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db)
    create_team_member(db, email=current_user.email, team_id=team.id)
    new_member = create_user(db)
    data = {"email": new_member.email}
    response = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/members", json=jsonable_encoder(data)
    )
    response.status_code == status.HTTP_403_FORBIDDEN


def test_add_existing_team_member_to_team(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify attempt to add existing team member to team again fails."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_user(db)
    create_team_member(db, email=team_member.email, team_id=team.id)
    data = {"email": team_member.email}
    r = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/members", json=jsonable_encoder(data)
    )
    assert 400 == r.status_code


def test_add_new_team_member_with_unused_email(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify attempt to add team member with email not in database properly handled."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    data = {"email": "email@notindb.doh"}
    r = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/members", json=jsonable_encoder(data)
    )
    assert 404 == r.status_code


def test_add_team_members(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    team = create_team(db, owner_id=current_user.id)
    new_member1 = create_user(db)
    new_member2 = create_user(db)
    new_member3 = create_user(db)
    data = [new_member1.id, new_member2.id, new_member3.id]
    r = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/members/multi",
        json=jsonable_encoder(data),
    )
    assert 201 == r.status_code
    response_data = r.json()
    len(response_data) == 3


def test_remove_team_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify team owner can remove a team member."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_team_member(db, team_id=team.id)
    r = client.delete(f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}")
    assert r.status_code == 200
    removed_team_member = r.json()
    assert str(team_member.id) == removed_team_member["id"]
    assert str(team_member.member_id) == removed_team_member["member_id"]


def test_remove_team_member_by_unauthorized_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify attempt to remove team member by non-owner fails."""
    owner = create_user(db)
    team = create_team(db, owner_id=owner.id)
    team_member = create_team_member(db, team_id=team.id)
    r = client.delete(f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}")
    assert r.status_code == 403
