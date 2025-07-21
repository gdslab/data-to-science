import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas.role import Role
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
    assert team_member.role == Role.VIEWER


def test_create_team_member_with_owner_role(db: Session) -> None:
    """Verify a new team member can be added with "owner" role."""
    user = create_user(db)
    team = create_team(db, owner_id=user.id)
    team_member = crud.team_member.get_team_member_by_id(
        db, user_id=user.id, team_id=team.id
    )
    assert team_member
    assert team_member.role == Role.OWNER


def test_create_duplicate_team_member(db: Session) -> None:
    """Verify cannot add user more than once to a team."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    user = create_user(db)
    create_team_member(db, email=user.email, team_id=team.id)
    with pytest.raises(IntegrityError):
        create_team_member(db, email=user.email, team_id=team.id)


def test_create_multi_team_members(db: Session) -> None:
    """Verify multiple team members can be added to a team."""
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
    """Verify duplicate team members are not added to the team when adding multiple members."""
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
    """Verify new team members are added to projects when a team is assigned to them."""
    # Create team
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Create project and assign team to it
    project1 = create_project(db, owner_id=team_owner.id, team_id=team.id)
    project2 = create_project(db, owner_id=team_owner.id, team_id=team.id)
    # Create three new team members
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    # Add new team members
    new_team_members = crud.team_member.create_multi_with_team(
        db,
        team_members=[user1.id, user2.id, user3.id, user3.id, team_owner.id],
        team_id=team.id,
    )
    # Fetch project members
    project_members1 = crud.project_member.get_list_of_project_members(
        db, project_uuid=project1.id
    )
    project_members2 = crud.project_member.get_list_of_project_members(
        db, project_uuid=project2.id
    )
    assert new_team_members
    assert len(new_team_members) == 4  # Three new team members plus owner
    assert project_members1 and project_members2
    # Four team members * two projects
    assert len(project_members1) + len(project_members2) == len(new_team_members) * 2
    for project_member in project_members1:
        assert project_member.member_id in [team_owner.id, user1.id, user2.id, user3.id]
        assert project_member.project_id == project1.id
    for project_member in project_members2:
        assert project_member.member_id in [team_owner.id, user1.id, user2.id, user3.id]
        assert project_member.project_id == project2.id


def test_no_duplicate_project_members_when_multiple_teams_assigned(db: Session) -> None:
    """Verify no duplicate project members when multiple teams are assigned to a project."""
    # Create two teams owned by same user
    team_owner = create_user(db)
    team1 = create_team(db, owner_id=team_owner.id)
    team2 = create_team(db, owner_id=team_owner.id)
    # Add same team members to both teams starting with team owner
    duplicate_team_members = []
    duplicate_team_members.append(team_owner.id)
    for i in range(0, 5):
        user = create_user(db)
        duplicate_team_members.append(user.id)
        create_team_member(db, email=user.email, team_id=team1.id)
        create_team_member(db, email=user.email, team_id=team2.id)
    # Add one additional team member to team2
    extra_team_member = create_user(db)
    create_team_member(db, email=extra_team_member.email, team_id=team2.id)
    # Create project with team1 association initially
    project = create_project(db, team_id=team1.id, owner_id=team_owner.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert len(project_members) == 6
    for project_member in project_members:
        assert project_member.member_id in duplicate_team_members
    # Remove team1 association from project
    updated_project = crud.project.update(
        db, db_obj=project, obj_in=schemas.ProjectUpdate(team_id=None)
    )
    assert updated_project.team_id is None
    project_members_after_team_removal = (
        crud.project_member.get_list_of_project_members(db, project_uuid=project.id)
    )
    assert len(project_members_after_team_removal) == 6
    # Assign team2 to the project
    crud.project.update_project(
        db,
        project_obj=project,
        project_in=schemas.ProjectUpdate(team_id=team2.id),
        project_id=project.id,
        user_id=team_owner.id,
    )
    project_members_after_new_team_assignment = (
        crud.project_member.get_list_of_project_members(db, project_uuid=project.id)
    )
    crud.team_member.get_list_of_team_members(db, team_id=team2.id)
    assert len(project_members_after_new_team_assignment) == 7
    duplicate_team_members.append(extra_team_member.id)
    for project_member in project_members_after_new_team_assignment:
        assert project_member.member_id in duplicate_team_members


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
    assert hasattr(member, "full_name")
    assert member.full_name == f"{user.first_name} {user.last_name}"
    assert hasattr(member, "email")
    assert member.email == user.email
    assert member.role == Role.VIEWER
    assert hasattr(member, "profile_url")  # url to profile image or None


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
    assert hasattr(member, "full_name")
    assert member.full_name == f"{user.first_name} {user.last_name}"
    assert hasattr(member, "email")
    assert member.email == user.email
    assert member.role == Role.VIEWER
    assert hasattr(member, "profile_url")  # url to profile image or None


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
        if team.owner_id == team_member.member_id:
            assert team_member.role == Role.OWNER
        else:
            assert team_member.role == Role.VIEWER


def test_update_team_member_role(db: Session) -> None:
    """Elevate team member from "viewer" role to "owner" role."""
    team_creator = create_user(db)
    team = create_team(db, owner_id=team_creator.id)
    member = create_team_member(db, team_id=team.id)
    assert member.role == Role.VIEWER
    team_member_in = schemas.TeamMemberUpdate(role=Role.OWNER)
    member_updated = crud.team_member.update(db, db_obj=member, obj_in=team_member_in)
    team_creator_member = crud.team_member.get_team_member_by_id(
        db, user_id=team_creator.id, team_id=team.id
    )
    assert team_creator_member
    assert team_creator_member.role == Role.OWNER
    assert member_updated
    assert member_updated.role == Role.OWNER


def test_update_team_member_role_also_updates_project_member_role(db: Session) -> None:
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Create two team members with "viewer" role
    team_member_viewer_to_owner = create_team_member(db, team_id=team.id)
    team_member_viewer_to_manager = create_team_member(db, team_id=team.id)
    # Create project and assign team to it
    project = create_project(db, owner_id=team_owner.id, team_id=team.id)
    # Update team member role to "owner"
    team_member_owner_in = schemas.TeamMemberUpdate(role=Role.OWNER)
    member_owner_updated = crud.team_member.update_team_member(
        db,
        team_member_in=team_member_owner_in,
        team_member_id=team_member_viewer_to_owner.id,
    )
    # Update team member role to "manager"
    team_member_manager_in = schemas.TeamMemberUpdate(role=Role.MANAGER)
    member_manager_updated = crud.team_member.update_team_member(
        db,
        team_member_in=team_member_manager_in,
        team_member_id=team_member_viewer_to_manager.id,
    )
    # Fetch project members
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert member_owner_updated
    assert member_owner_updated.role == Role.OWNER
    assert member_manager_updated
    assert member_manager_updated.role == Role.MANAGER
    assert project_members
    assert len(project_members) == 3
    # Project should have two members with "owner" role and one with "manager" role
    for project_member in project_members:
        if project_member.member_id == team_owner.id:
            assert project_member.role == Role.OWNER
        elif project_member.member_id == team_member_viewer_to_owner.id:
            assert project_member.role == Role.OWNER
        elif project_member.member_id == team_member_viewer_to_manager.id:
            assert project_member.role == Role.MANAGER


def test_update_team_member_role_of_team_creator(db: Session) -> None:
    """Verify team creator cannot be demoted to "viewer" role."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_member = crud.team_member.get_team_member_by_id(
        db, user_id=team_owner.id, team_id=team.id
    )
    assert team_member
    assert team_member.role == Role.OWNER
    team_member_in = schemas.TeamMemberUpdate(role=Role.VIEWER)
    member_updated = crud.team_member.update_team_member(
        db, team_member_in=team_member_in, team_member_id=team_member.id
    )
    assert member_updated is None
    team_member_after_update = crud.team_member.get_team_member_by_id(
        db, user_id=team_owner.id, team_id=team.id
    )
    assert team_member_after_update
    assert team_member_after_update.role == Role.OWNER


def test_update_team_member_role_of_project_creator_does_not_update_project_member_role(
    db: Session,
) -> None:
    """Verify updating team member role of project creator does not update project member role."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_member_and_project_owner = create_user(db)
    team_member = create_team_member(
        db,
        email=team_member_and_project_owner.email,
        team_id=team.id,
        role=Role.MANAGER,
    )
    project = create_project(
        db, owner_id=team_member_and_project_owner.id, team_id=team.id
    )
    # Attempt to downgrade project member role to "viewer"
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=team_member_and_project_owner.id
    )
    assert project_member
    project_member_in = schemas.ProjectMemberUpdate(role=Role.VIEWER)
    project_member_updated_response = crud.project_member.update_project_member(
        db, project_member_obj=project_member, project_member_in=project_member_in
    )
    # Confirm project member role was not updated and project member still has "owner" role
    assert project_member_updated_response["response_code"] == 400
    assert (
        project_member_updated_response["message"]
        == "Cannot change project creator role"
    )
    assert project_member_updated_response["result"] is None


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


def test_remove_team_creator(db: Session) -> None:
    """Verify attempt to remove team creator fails."""
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Attempt to remove team creator
    removed_member = crud.team_member.remove_team_member(
        db, member_id=team_owner.id, team_id=team.id
    )
    assert removed_member is None
    # Verify team creator still exists
    team_owner_after_remove = crud.team_member.get_team_member_by_id(
        db, user_id=team_owner.id, team_id=team.id
    )
    assert team_owner_after_remove
    assert team_owner_after_remove.role == Role.OWNER
