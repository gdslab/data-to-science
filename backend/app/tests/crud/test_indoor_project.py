from datetime import datetime
from typing import List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import crud
from app.core.exceptions import PermissionDenied, ResourceNotFound
from app.models.project_type import ProjectType
from app.schemas.indoor_project import IndoorProjectCreate, IndoorProjectUpdate
from app.schemas.role import Role
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_indoor_project_with_all_fields(db: Session) -> None:
    """
    Test creating an indoor project with required and optional fields.
    """
    # required fields
    title = "Test Indoor Project"
    description = "Test indoor phenotyping project"
    # optional fields
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 6, 30)
    # project owner
    owner = create_user(db)
    # indoor project creation object
    indoor_project_in = IndoorProjectCreate(
        title=title, description=description, start_date=start_date, end_date=end_date
    )
    # create indoor project in database
    indoor_project = crud.indoor_project.create_with_owner(
        db, obj_in=indoor_project_in, owner_id=owner.id
    )

    assert indoor_project.id
    assert indoor_project.title == title
    assert indoor_project.description == description
    assert indoor_project.start_date == start_date
    assert indoor_project.end_date == end_date
    assert indoor_project.owner_id == owner.id
    assert indoor_project.is_active is True
    assert indoor_project.deactivated_at is None


def test_create_indoor_project_without_optional_fields(db: Session) -> None:
    """
    Test creating an indoor project with only required fields.
    """
    # required fields
    title = "Test Indoor Project"
    description = "Test indoor phenotyping project"

    # project owner
    owner = create_user(db)

    # indoor project creation model
    indoor_project_in = IndoorProjectCreate(title=title, description=description)

    # create indoor project in database
    indoor_project = crud.indoor_project.create_with_owner(
        db, obj_in=indoor_project_in, owner_id=owner.id
    )

    assert indoor_project.id
    assert indoor_project.title == title
    assert indoor_project.description == description
    assert indoor_project.start_date is None
    assert indoor_project.end_date is None
    assert indoor_project.owner_id == owner.id
    assert indoor_project.is_active is True
    assert indoor_project.deactivated_at is None


def test_read_indoor_project(db: Session) -> None:
    """
    Test reading an existing indoor project.
    """
    # create indoor project in db with random values
    existing_indoor_project = create_indoor_project(db)

    # fetch indoor project from db
    indoor_project_from_db = crud.indoor_project.read_by_user_id(
        db,
        indoor_project_id=existing_indoor_project.id,
        user_id=existing_indoor_project.owner_id,
    )

    assert indoor_project_from_db
    assert indoor_project_from_db.id == existing_indoor_project.id
    assert indoor_project_from_db.title == existing_indoor_project.title
    assert indoor_project_from_db.description == existing_indoor_project.description
    assert indoor_project_from_db.start_date == existing_indoor_project.start_date
    assert indoor_project_from_db.end_date == existing_indoor_project.end_date
    assert indoor_project_from_db.owner_id == existing_indoor_project.owner_id
    assert indoor_project_from_db.is_active == existing_indoor_project.is_active
    assert (
        indoor_project_from_db.deactivated_at == existing_indoor_project.deactivated_at
    )


def test_read_indoor_projects(db: Session) -> None:
    """
    Test reading multiple existing indoor projects.
    """
    # create user that will own all indoor projects
    owner = create_user(db)

    # create three indoor projects in db with random values
    existing_indoor_project1 = create_indoor_project(db, owner_id=owner.id)
    existing_indoor_project2 = create_indoor_project(db, owner_id=owner.id)
    existing_indoor_project3 = create_indoor_project(db, owner_id=owner.id)

    # fetch indoor projects from db
    indoor_projects_from_db = crud.indoor_project.read_multi_by_user_id(
        db, user_id=owner.id
    )

    assert indoor_projects_from_db
    assert isinstance(indoor_projects_from_db, List)
    assert len(indoor_projects_from_db) == 3
    for indoor_project in indoor_projects_from_db:
        assert indoor_project.id in [
            existing_indoor_project1.id,
            existing_indoor_project2.id,
            existing_indoor_project3.id,
        ]


def test_update_indoor_project(db: Session) -> None:
    """
    Test updating an existing indoor project.
    """
    # create indoor project in db with random values
    existing_indoor_project = create_indoor_project(db)

    # get old title, description, start_date, and end_date
    old_title = existing_indoor_project.title
    old_description = existing_indoor_project.description
    old_start_date = existing_indoor_project.start_date
    old_end_date = existing_indoor_project.end_date

    # new values
    new_title = "Update Title"
    new_description = "Update Description"
    new_start_date = datetime(2024, 5, 1)
    new_end_date = datetime(2024, 10, 1)

    # indoor project update model
    indoor_project_update_in = IndoorProjectUpdate(
        title=new_title,
        description=new_description,
        start_date=new_start_date,
        end_date=new_end_date,
    )

    # update record in database
    updated_indoor_project = crud.indoor_project.update(
        db, db_obj=existing_indoor_project, obj_in=indoor_project_update_in
    )

    assert updated_indoor_project
    assert updated_indoor_project.id == existing_indoor_project.id
    assert updated_indoor_project.title == new_title
    assert updated_indoor_project.description == new_description
    assert updated_indoor_project.start_date == new_start_date
    assert updated_indoor_project.end_date == new_end_date


def test_deactivate_indoor_project(db: Session) -> None:
    """
    Test deactivating an existing indoor project.
    """
    # create indoor project in db with random values
    existing_indoor_project = create_indoor_project(db)

    # deactivate indoor project in db
    deactivated_indoor_project = crud.indoor_project.deactivate(
        db, indoor_project_id=existing_indoor_project.id
    )

    assert deactivated_indoor_project
    assert deactivated_indoor_project.id == existing_indoor_project.id
    assert deactivated_indoor_project.is_active is False
    assert deactivated_indoor_project.deactivated_at
    assert deactivated_indoor_project.deactivated_at < datetime.utcnow()


def test_get_with_permission_owner_can_access_with_viewer_permission(
    db: Session,
) -> None:
    """
    Test that project owner can access project with VIEWER permission level.
    """
    # Create indoor project
    indoor_project = create_indoor_project(db)

    # Owner should be able to access with VIEWER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=indoor_project.owner_id,
        required_permission=Role.VIEWER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.OWNER.value


def test_get_with_permission_owner_can_access_with_manager_permission(
    db: Session,
) -> None:
    """
    Test that project owner can access project with MANAGER permission level.
    """
    # Create indoor project
    indoor_project = create_indoor_project(db)

    # Owner should be able to access with MANAGER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=indoor_project.owner_id,
        required_permission=Role.MANAGER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.OWNER.value


def test_get_with_permission_owner_can_access_with_owner_permission(
    db: Session,
) -> None:
    """
    Test that project owner can access project with OWNER permission level.
    """
    # Create indoor project
    indoor_project = create_indoor_project(db)

    # Owner should be able to access with OWNER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=indoor_project.owner_id,
        required_permission=Role.OWNER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.OWNER.value


def test_get_with_permission_manager_can_access_with_viewer_permission(
    db: Session,
) -> None:
    """
    Test that project manager can access project with VIEWER permission level.
    """
    # Create indoor project and manager user
    indoor_project = create_indoor_project(db)
    manager = create_user(db)

    # Add manager as project member
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=manager.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Manager should be able to access with VIEWER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=manager.id,
        required_permission=Role.VIEWER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.MANAGER.value


def test_get_with_permission_manager_can_access_with_manager_permission(
    db: Session,
) -> None:
    """
    Test that project manager can access project with MANAGER permission level.
    """
    # Create indoor project and manager user
    indoor_project = create_indoor_project(db)
    manager = create_user(db)

    # Add manager as project member
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=manager.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Manager should be able to access with MANAGER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=manager.id,
        required_permission=Role.MANAGER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.MANAGER.value


def test_get_with_permission_manager_cannot_access_with_owner_permission(
    db: Session,
) -> None:
    """
    Test that project manager cannot access project with OWNER permission level.
    """
    # Create indoor project and manager user
    indoor_project = create_indoor_project(db)
    manager = create_user(db)

    # Add manager as project member
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=manager.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Manager should not be able to access with OWNER permission
    with pytest.raises(PermissionDenied) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=indoor_project.id,
            user_id=manager.id,
            required_permission=Role.OWNER,
        )

    assert "owner role or higher" in str(exc_info.value.detail).lower()


def test_get_with_permission_viewer_can_access_with_viewer_permission(
    db: Session,
) -> None:
    """
    Test that project viewer can access project with VIEWER permission level.
    """
    # Create indoor project and viewer user
    indoor_project = create_indoor_project(db)
    viewer = create_user(db)

    # Add viewer as project member
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=viewer.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Viewer should be able to access with VIEWER permission
    result = crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project.id,
        user_id=viewer.id,
        required_permission=Role.VIEWER,
    )

    assert result is not None
    assert result.id == indoor_project.id
    assert getattr(result, "role", None) == Role.VIEWER.value


def test_get_with_permission_viewer_cannot_access_with_manager_permission(
    db: Session,
) -> None:
    """
    Test that project viewer cannot access project with MANAGER permission level.
    """
    # Create indoor project and viewer user
    indoor_project = create_indoor_project(db)
    viewer = create_user(db)

    # Add viewer as project member
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=viewer.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Viewer should not be able to access with MANAGER permission
    with pytest.raises(PermissionDenied) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=indoor_project.id,
            user_id=viewer.id,
            required_permission=Role.MANAGER,
        )

    assert "manager role or higher" in str(exc_info.value.detail).lower()


def test_get_with_permission_viewer_cannot_access_with_owner_permission(
    db: Session,
) -> None:
    """
    Test that project viewer cannot access project with OWNER permission level.
    """
    # Create indoor project and viewer user
    indoor_project = create_indoor_project(db)
    viewer = create_user(db)

    # Add viewer as project member
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=viewer.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Viewer should not be able to access with OWNER permission
    with pytest.raises(PermissionDenied) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=indoor_project.id,
            user_id=viewer.id,
            required_permission=Role.OWNER,
        )

    assert "owner role or higher" in str(exc_info.value.detail).lower()


def test_get_with_permission_non_member_cannot_access(db: Session) -> None:
    """
    Test that non-member user cannot access project.
    """
    # Create indoor project and non-member user
    indoor_project = create_indoor_project(db)
    non_member = create_user(db)

    # Non-member should not be able to access
    with pytest.raises(PermissionDenied) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=indoor_project.id,
            user_id=non_member.id,
            required_permission=Role.VIEWER,
        )

    assert "not a member" in str(exc_info.value.detail).lower()


def test_get_with_permission_project_not_found(db: Session) -> None:
    """
    Test that ResourceNotFound is raised when project doesn't exist.
    """
    # Create user
    user = create_user(db)

    # Random UUID that doesn't exist
    non_existent_id = uuid4()

    # Should raise ResourceNotFound
    with pytest.raises(ResourceNotFound) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=non_existent_id,
            user_id=user.id,
            required_permission=Role.VIEWER,
        )

    assert "indoor project not found" in str(exc_info.value.detail).lower()


def test_get_with_permission_inactive_project_raises_not_found(db: Session) -> None:
    """
    Test that ResourceNotFound is raised when project is inactive.
    """
    # Create and deactivate indoor project
    indoor_project = create_indoor_project(db)
    crud.indoor_project.deactivate(db, indoor_project_id=indoor_project.id)

    # Owner should not be able to access inactive project
    with pytest.raises(ResourceNotFound) as exc_info:
        crud.indoor_project.get_with_permission(
            db,
            indoor_project_id=indoor_project.id,
            user_id=indoor_project.owner_id,
            required_permission=Role.VIEWER,
        )

    assert "indoor project not found" in str(exc_info.value.detail).lower()
