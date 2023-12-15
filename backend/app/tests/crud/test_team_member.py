import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.project import create_project
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_create_team_member(db: Session) -> None:
    """Verify a new team member can be added to an existing team."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    user = create_user(db)
    team_member = create_team_member(db, email=user.email, team_id=team.id)
    assert team_member
    assert user.id == team_member.member_id
    assert team.id == team_member.team_id


def test_create_duplicate_team_member(db: Session) -> None:
    """Verify cannot add user more than once to a team."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    user = create_user(db)
    create_team_member(db, email=user.email, team_id=team.id)
    with pytest.raises(IntegrityError):
        create_team_member(db, email=user.email, team_id=team.id)


def test_create_multi_team_members(db: Session) -> None:
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    new_team_members = crud.team_member.create_multi_with_team(
        db, team_members=[user1.id, user2.id, user3.id], team_id=team.id
    )
    assert new_team_members
    assert len(new_team_members) == 4


def test_create_mutli_team_members_with_existing_member(db: Session) -> None:
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    new_team_members = crud.team_member.create_multi_with_team(
        db,
        team_members=[user1.id, user2.id, user3.id, team_owner.id, user3.id],
        team_id=team.id,
    )
    assert new_team_members
    assert len(new_team_members) == 4


def test_create_multi_team_members_adds_project_members(db: Session) -> None:
    # create team
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # create project and assign team to it
    project = create_project(db, owner_id=team_owner.id, team_id=team.id)
    # create three new team members
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    # add new team members
    new_team_members = crud.team_member.create_multi_with_team(
        db,
        team_members=[user1.id, user2.id, user3.id, team_owner.id, user3.id],
        team_id=team.id,
    )
    # fetch project members
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id
    )
    assert new_team_members
    assert len(new_team_members) == 4  # three new team members plus owner
    assert project_members
    assert len(project_members) == len(new_team_members)
    for project_member in project_members:
        assert project_member.member_id in [team_owner.id, user1.id, user2.id, user3.id]


def test_get_team_member_by_email(db: Session) -> None:
    """Verify a team member can be retrieved by email."""
    team = create_team(db)
    user = create_user(db)
    create_team_member(db, email=user.email, team_id=team.id)
    member = crud.team_member.get_team_member_by_email(
        db, email=user.email, team_id=team.id
    )
    assert member
    assert member.member_id == user.id
    assert member.team_id == team.id
    assert member.full_name == f"{user.first_name} {user.last_name}"
    assert member.email == user.email


def test_get_team_member_by_id(db: Session) -> None:
    """Verify a team member can be retrieved by id."""
    team = create_team(db)
    user = create_user(db)
    create_team_member(db, email=user.email, team_id=team.id)
    member = crud.team_member.get_team_member_by_id(
        db, user_id=user.id, team_id=team.id
    )
    assert member
    assert member.member_id == user.id
    assert member.team_id == team.id
    assert member.full_name == f"{user.first_name} {user.last_name}"
    assert member.email == user.email


def test_get_list_of_team_members(db: Session) -> None:
    """Verify a team id can return a list of team members."""
    team = create_team(db)
    member1 = create_team_member(db, team_id=team.id)
    member2 = create_team_member(db, team_id=team.id)
    team_members = crud.team_member.get_list_of_team_members(db, team_id=team.id)
    assert type(team_members) is list
    assert len(team_members) == 3  # owner + two added team members
    for team_member in team_members:
        assert (
            team.owner_id == team_member.member_id
            or member1.member_id == team_member.member_id
            or member2.member_id == team_member.member_id
        )


def test_remove_team_member_by_id(db: Session) -> None:
    """Verify removal of team member by team owner."""
    owner = create_user(db)
    team = create_team(db, owner_id=owner.id)
    member = create_team_member(db, team_id=team.id)
    assert member
    member_removed = crud.team_member.remove_team_member(
        db, member_id=member.member_id, team_id=team.id
    )
    assert member_removed
    member_in_db_after_removed = crud.team_member.get_team_member_by_id(
        db, user_id=member.member_id, team_id=team.id
    )
    assert member_in_db_after_removed is None
    assert member_removed.id == member.id
    assert member_removed.member_id == member.member_id


def test_remove_team_member_removes_from_project_members(db: Session) -> None:
    owner = create_user(db)
    team = create_team(db, owner_id=owner.id)
    project = create_project(db, owner_id=owner.id, team_id=team.id)
    member1 = create_team_member(db, team_id=team.id)
    for i in range(0, 4):
        create_team_member(db, team_id=team.id)
    member_removed = crud.team_member.remove_team_member(
        db, member_id=member1.member_id, team_id=team.id
    )
    assert member_removed
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_id=project.id, member_id=member1.member_id
    )
    assert project_member is None
