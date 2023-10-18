from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_project_member(db: Session) -> None:
    """Verify a new project member can be added to an existing project."""
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    user = create_user(db)
    project_member = create_project_member(db, member_id=user.id, project_id=project.id)
    assert project_member
    assert user.id == project_member.member_id
    assert project.id == project_member.project_id


def test_get_list_of_project_members(db: Session) -> None:
    project = create_project(db)
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


def test_get_list_of_project_members_from_deactivated_project(db: Session) -> None:
    project = create_project(db)
    create_project_member(db, project_id=project.id)
    create_project_member(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id
    )
    assert type(project_members) is list
    assert len(project_members) == 0
