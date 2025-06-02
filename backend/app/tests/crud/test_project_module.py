from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.project import create_project


def test_get_project_modules_by_project_id(db: Session) -> None:
    """Test retrieving all module types with their enabled status for a project."""
    # Create a project
    project = create_project(db)

    # Get all modules for the project
    modules = crud.project_module.get_project_modules_by_project_id(
        db, project_id=project.id
    )

    # Verify the response structure
    assert isinstance(modules, List)
    assert len(modules) > 0

    # Check each module has the expected fields
    for module in modules:
        assert "module_name" in module
        assert "label" in module
        assert "description" in module
        assert "required" in module
        assert "enabled" in module
        assert "sort_order" in module

        # Required modules should always be enabled
        if module["required"]:
            assert module["enabled"] is True


def test_update_project_module(db: Session) -> None:
    """Test updating a project module's enabled status."""
    # Create a project
    project = create_project(db)

    # Get all modules for the project
    modules = crud.project_module.get_project_modules_by_project_id(
        db, project_id=project.id
    )

    # Find a non-required module to test with
    test_module = next((m for m in modules if not m["required"]), None)

    assert test_module is not None, "No non-required modules found for testing"

    # Test enabling the module
    updated_module = crud.project_module.update_project_module(
        db, project_id=project.id, module_name=test_module["module_name"], enabled=True
    )
    assert updated_module is not None
    assert updated_module.enabled is True

    # Test disabling the module
    updated_module = crud.project_module.update_project_module(
        db, project_id=project.id, module_name=test_module["module_name"], enabled=False
    )
    assert updated_module is not None
    assert updated_module.enabled is False


def test_update_nonexistent_project_module(db: Session) -> None:
    """Test updating a project module that doesn't exist."""
    # Create a project
    project = create_project(db)

    # Try to update a non-existent module
    updated_module = crud.project_module.update_project_module(
        db, project_id=project.id, module_name="nonexistent_module", enabled=True
    )

    # Should return None for non-existent module
    assert updated_module is None
