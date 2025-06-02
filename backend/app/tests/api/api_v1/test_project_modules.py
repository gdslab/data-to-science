from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.role import Role
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_read_project_modules_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading project modules as project owner."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert isinstance(modules, list)

    # Verify each module has required fields
    for module in modules:
        assert "module_name" in module
        assert "label" in module
        assert "description" in module
        assert "required" in module
        assert "enabled" in module
        assert "sort_order" in module


def test_read_project_modules_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading project modules as project manager."""
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)

    # Add current user as project manager
    create_project_member(
        db, project_id=project.id, member_id=current_user.id, role=Role.MANAGER
    )

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert isinstance(modules, list)


def test_read_project_modules_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading project modules as project viewer."""
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)

    # Add current user as project viewer
    create_project_member(
        db, project_id=project.id, member_id=current_user.id, role=Role.VIEWER
    )

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert isinstance(modules, list)
    # Verify each module has required fields
    for module in modules:
        assert "module_name" in module
        assert "label" in module
        assert "description" in module
        assert "required" in module
        assert "enabled" in module
        assert "sort_order" in module


def test_read_project_modules_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading project modules without project role."""
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_module_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating project module as project owner."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)

    # Get initial modules to find a module to update
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert len(modules) > 0

    # Update first non-required module
    module_to_update = next(m for m in modules if not m["required"])
    module_name = module_to_update["module_name"]

    update_data = {"enabled": True}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/modules/{module_name}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK
    updated_module = response.json()
    assert updated_module["module_name"] == module_name
    assert updated_module["enabled"] is True


def test_update_project_module_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating project module as project manager."""
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)

    # Add current user as project manager
    create_project_member(
        db, project_id=project.id, member_id=current_user.id, role=Role.MANAGER
    )

    # Get initial modules to find a module to update
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert len(modules) > 0

    # Update first non-required module
    module_to_update = next(m for m in modules if not m["required"])
    module_name = module_to_update["module_name"]

    update_data = {"enabled": True}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/modules/{module_name}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_module_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating project module as project viewer."""
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)

    # Add current user as project viewer
    create_project_member(
        db, project_id=project.id, member_id=current_user.id, role=Role.VIEWER
    )

    # Get initial modules to find a module to update
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_200_OK
    modules = response.json()
    assert len(modules) > 0

    # Update first non-required module
    module_to_update = next(m for m in modules if not m["required"])
    module_name = module_to_update["module_name"]

    update_data = {"enabled": True}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/modules/{module_name}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_module_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating project module without project role."""
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)

    # Get initial modules to find a module to update
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/modules")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_nonexistent_project_module(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating a module that doesn't exist."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)

    update_data = {"enabled": True}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/modules/nonexistent_module",
        json=update_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
