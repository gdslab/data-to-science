import pytest
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.project_member import ProjectMemberUpdate
from app.schemas.team_member import Role
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_create_project_member(db: Session) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    user = create_user(db)
    project_member = create_project_member(db, member_id=user.id, project_id=project.id)
    assert project_member
    assert user.id == project_member.member_id
    assert project.id == project_member.project_id
    assert project_member.role == "viewer"  # default role


def test_create_project_members_with_different_roles(db: Session) -> None:
    project_owner = create_user(db)
    project_manager = create_user(db)
    project_viewer = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    manager_role = create_project_member(
        db, member_id=project_manager.id, project_id=project.id, role="manager"
    )
    viewer_role = create_project_member(
        db, member_id=project_viewer.id, project_id=project.id
    )
    owner_in_db = crud.project_member.get_by_project_and_member_id(
        db, project_id=project.id, member_id=project_owner.id
    )
    manager_in_db = crud.project_member.get(db, id=manager_role.id)
    viewer_in_db = crud.project_member.get(db, id=viewer_role.id)
    assert owner_in_db and manager_in_db and viewer_in_db
    assert owner_in_db.role == "owner"
    assert manager_in_db.role == "manager"
    assert viewer_in_db.role == "viewer"


def test_create_project_members(db: Session) -> None:
    project_owner = create_user(db)
    team = create_team(db, owner_id=project_owner.id)
    team_members = []
    for i in range(0, 5):
        team_member = create_team_member(db, team_id=team.id)
        team_members.append((team_member.member_id, Role.MEMBER))
    project = create_project(db, owner_id=project_owner.id, team_id=team.id)
    project_members = crud.project_member.create_multi_with_project(
        db, new_members=team_members, project_id=project.id
    )
    assert isinstance(project_members, list)
    assert len(project_members) == 6  # owner + five added project members


def test_get_project_member(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    owner_in_db = crud.project_member.get_by_project_and_member_id(
        db, member_id=owner.id, project_id=project.id
    )
    assert owner_in_db
    assert owner_in_db.member_id == owner.id
    assert owner_in_db.role == "owner"


def test_get_list_of_project_members(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    member1 = create_project_member(db, project_id=project.id)
    member2 = create_project_member(db, project_id=project.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id
    )
    assert type(project_members) is list
    assert len(project_members) == 3  # owner + two added project members
    for project_member in project_members:
        assert (
            project.owner_id == project_member.member_id
            or member1.member_id == project_member.member_id
            or member2.member_id == project_member.member_id
        )
        assert (
            project_member.member_id == owner.id
            and project_member.role == "owner"
            or project_member.member_id != owner.id
            and project_member.role == "viewer"
        )
        assert project_member.full_name
        assert project_member.email


def test_get_list_of_project_members_with_specific_role(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    member1 = create_project_member(db, project_id=project.id, role="manager")
    member2 = create_project_member(db, project_id=project.id, role="manager")
    member3 = create_project_member(db, project_id=project.id, role="viewer")
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id, role="manager"
    )
    assert type(project_members) is list
    assert len(project_members) == 2
    for project_member in project_members:
        assert project_member.role == "manager"


def test_get_list_of_project_members_from_deactivated_project(db: Session) -> None:
    project = create_project(db)
    create_project_member(db, project_id=project.id)
    create_project_member(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id, user_id=project.owner_id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id
    )
    assert type(project_members) is list
    assert len(project_members) == 0


def test_update_project_member(db: Session) -> None:
    project_member = create_project_member(db, role="viewer")
    project_member_in_update = ProjectMemberUpdate(role="manager")
    project_member_update = crud.project_member.update_project_member(
        db,
        project_member_obj=project_member,
        project_member_in=project_member_in_update,
    )
    project_member_update = project_member_update["result"]
    assert project_member_update.id == project_member.id
    assert project_member_update.role == "manager"


def test_update_role_for_only_project_owner(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    project_owner = crud.project_member.get_by_project_and_member_id(
        db, project_id=project.id, member_id=owner.id
    )
    project_owner_in_update = ProjectMemberUpdate(role="manager")
    project_owner_update = crud.project_member.update_project_member(
        db, project_member_obj=project_owner, project_member_in=project_owner_in_update
    )
    assert project_owner_update["result"] is None


def test_delete_project_member(db: Session) -> None:
    project_member = create_project_member(db, role="viewer")
    project_member2 = crud.project_member.remove(db, id=project_member.id)
    project_member3 = crud.project_member.get(db, id=project_member.id)
    assert project_member3 is None
    assert project_member2
    assert project_member2.id == project_member.id
    assert project_member2.role == project_member.role
    assert project_member2.member_id == project_member.member_id


def test_delete_project_members(db: Session) -> None:
    project_owner = create_user(db)
    team = create_team(db, owner_id=project_owner.id)
    project = create_project(db, team_id=team.id, owner_id=project_owner.id)
    other_project = create_project(db, team_id=team.id, owner_id=project_owner.id)
    for i in range(0, 5):
        create_project_member(db, project_id=project.id)
        create_project_member(db, project_id=other_project.id)
    removed_project_members = crud.project_member.delete_multi(
        db, project_id=project.id, team_id=team.id
    )
    assert isinstance(removed_project_members, list)
    assert len(removed_project_members) == 5
    for project_member in removed_project_members:
        assert crud.project_member.get(db, id=project_member.id) is None


def test_assign_project_member_invalid_role(db: Session) -> None:
    with pytest.raises(DataError):
        create_project_member(db, role="invalid-role")
