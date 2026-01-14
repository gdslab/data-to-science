from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project_type import ProjectType
from app.schemas.role import Role
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_can_read_indoor_project_owner(db: Session) -> None:
    """
    Test that indoor project owner can read their project.
    """
    # create indoor project and owner
    owner = create_user(db)
    indoor_project = create_indoor_project(db, owner_id=owner.id)

    # test that owner can read the project
    result = deps.can_read_indoor_project(
        indoor_project_id=indoor_project.id, db=db, current_user=owner
    )

    assert result.id == indoor_project.id
    assert result.owner_id == owner.id


def test_can_read_indoor_project_member(db: Session) -> None:
    """
    Test that indoor project member can read the project.
    """
    # create indoor project and owner
    owner = create_user(db)
    member = create_user(db)
    indoor_project = create_indoor_project(db, owner_id=owner.id)

    # add member to the project
    create_project_member(
        db,
        member_id=member.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
        role=Role.VIEWER,
    )

    # test that member can read the project
    result = deps.can_read_indoor_project(
        indoor_project_id=indoor_project.id, db=db, current_user=member
    )

    assert result.id == indoor_project.id
    assert result.owner_id == owner.id


def test_can_read_indoor_project_unauthorized(db: Session) -> None:
    """
    Test that unauthorized user cannot read indoor project.
    """
    # create indoor project owned by different user
    owner = create_user(db)
    unauthorized_user = create_user(db)
    indoor_project = create_indoor_project(db, owner_id=owner.id)

    # test that unauthorized user cannot read the project
    try:
        deps.can_read_indoor_project(
            indoor_project_id=indoor_project.id, db=db, current_user=unauthorized_user
        )
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
        assert "you are not a member of this indoor project" in e.detail.lower()


def test_can_read_indoor_project_not_found(db: Session) -> None:
    """
    Test that non-existent indoor project returns 404.
    """
    user = create_user(db)
    fake_project_id = uuid4()

    # test that non-existent project returns 404
    try:
        deps.can_read_indoor_project(
            indoor_project_id=fake_project_id, db=db, current_user=user
        )
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 404
        assert "indoor project not found" in e.detail.lower()
