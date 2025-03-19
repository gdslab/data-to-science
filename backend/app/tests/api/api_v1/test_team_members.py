from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.team_member import Role, TeamMemberUpdate
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
    assert len(response_data) == 4  # three new members plus owner


def test_get_team_members(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    current_user_tm = crud.team_member.get_team_member_by_email(
        db, email=current_user.email, team_id=team.id
    )
    assert current_user_tm
    team_member_ids = [str(current_user_tm.id)]
    for i in range(0, 3):
        team_member = create_team_member(db, team_id=team.id)
        team_member_ids.append(str(team_member.id))
    response = client.get(f"{settings.API_V1_STR}/teams/{team.id}/members")
    assert response.status_code == status.HTTP_200_OK
    fetched_team_members = response.json()
    assert type(fetched_team_members) == list
    assert len(fetched_team_members) == 4  # 3 added members + owner (current user)
    for tm in fetched_team_members:
        assert tm["id"] in team_member_ids


def test_update_team_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "owner"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "owner"


def test_update_team_member_role_to_viewer(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "viewer"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "viewer"


def test_update_team_member_role_to_manager(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "manager"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "manager"


def test_update_team_member_role_to_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team = create_team(db, owner_id=current_user.id)
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "owner"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "owner"


def test_update_team_member_role_to_manager_by_manager(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team as manager
    current_user_team_member = create_team_member(
        db, email=current_user.email, team_id=team.id
    )
    update_team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=current_user_team_member.id,
    )
    # Add new team member to team
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "manager"}
    # Attempt to update role of new team member to owner
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "manager"


def test_update_team_member_role_to_viewer_by_manager(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team as manager
    current_user_team_member = create_team_member(
        db, email=current_user.email, team_id=team.id
    )
    update_team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=current_user_team_member.id,
    )
    # Add new team member to team
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "viewer"}
    # Attempt to update role of new team member to owner
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "viewer"


def test_update_team_member_role_to_owner_by_manager_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team as manager
    current_user_team_member = create_team_member(
        db, email=current_user.email, team_id=team.id
    )
    update_team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=current_user_team_member.id,
    )
    # Add new team member to team
    team_member = create_team_member(db, team_id=team.id)
    data = {"role": "owner"}
    # Attempt to update role of new team member to owner
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_downgrade_team_member_with_owner_role_to_manager_by_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team owned by current user
    team = create_team(db, owner_id=current_user.id)
    # Add new team member to team and update role to owner
    team_member = create_team_member(db, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.OWNER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Attempt to downgrade team member with owner role to manager
    data = {"role": "manager"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "manager"


def test_downgrade_team_member_with_owner_role_to_viewer_by_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team owned by current user
    team = create_team(db, owner_id=current_user.id)
    # Add new team member to team and update role to owner
    team_member = create_team_member(db, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.OWNER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Attempt to downgrade team member with owner role to manager
    data = {"role": "viewer"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "viewer"


def test_downgrade_team_member_with_owner_role_to_manager_by_manager_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team and update role to manager
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Add new team member to team and update role to owner
    team_member2 = create_team_member(db, team_id=team.id)
    update_team_member2_in = TeamMemberUpdate(role=Role.OWNER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member2_in,
        team_member_id=team_member2.id,
    )
    # Attempt to downgrade team member with owner role to manager
    data = {"role": "manager"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member2.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_downgrade_team_member_with_manager_role_to_viewer_by_manager(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Add current user to team and update role to manager
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Add new team member to team and update role to manager
    team_member2 = create_team_member(db, team_id=team.id)
    update_team_member2_in = TeamMemberUpdate(role=Role.MANAGER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member2_in,
        team_member_id=team_member2.id,
    )
    # Attempt to downgrade team member with manager role to viewer
    data = {"role": "viewer"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member2.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["role"] == "viewer"


def test_downgrade_team_creator_with_owner_role_by_owner_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # Create team not owned by current user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_owner_team_member = crud.team_member.get_team_member_by_id(
        db, user_id=team_owner.id, team_id=team.id
    )
    assert team_owner_team_member is not None
    # Add current user to team and update role to owner
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.OWNER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Attempt to downgrade team creator with owner role to manager
    data = {"role": "manager"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_owner_team_member.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_non_creator_owner_can_update_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create team with owner and two additional members
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    team_member2 = create_team_member(db, team_id=team.id)
    # Update role of current user to owner
    crud.team_member.update(db, db_obj=team_member, obj_in={"role": Role.OWNER})
    # Attempt to update role of second team member to owner
    data = {"role": "owner"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member2.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_team_member = response.json()
    assert updated_team_member["member_id"] == str(team_member2.member_id)
    assert updated_team_member["role"] == "owner"


def test_non_creator_member_cannot_update_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create team with owner and two additional members
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    create_team_member(db, email=current_user.email, team_id=team.id)
    team_member2 = create_team_member(db, team_id=team.id)
    # Attempt to update role of second team member to owner
    data = {"role": "owner"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_member2.id}",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


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


def test_remove_team_creator_by_team_member_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create team owned by other user
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_owner_team_member = crud.team_member.get_team_member_by_id(
        db, user_id=team_owner.id, team_id=team.id
    )
    assert team_owner_team_member is not None
    # Add current user to team and update role to owner
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    team_member = create_team_member(db, email=current_user.email, team_id=team.id)
    update_team_member_in = TeamMemberUpdate(role=Role.OWNER)
    crud.team_member.update_team_member(
        db,
        team_member_in=update_team_member_in,
        team_member_id=team_member.id,
    )
    # Attempt to remove team creator
    r = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}/members/{team_owner_team_member.id}"
    )
    assert r.status_code == 403
