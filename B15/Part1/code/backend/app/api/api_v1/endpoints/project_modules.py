import logging
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

logger = logging.getLogger("__name__")

router = APIRouter()


@router.get("", response_model=List[schemas.ProjectModule])
def read_project_modules(
    project_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    """Retrieve list of modules for a project."""
    project_modules = crud.project_module.get_project_modules_by_project_id(
        db, project_id=project_id
    )
    if not project_modules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No modules found for this project",
        )
    return project_modules


@router.put("/{module_name}", response_model=schemas.ProjectModule)
def update_project_module(
    project_id: UUID,
    module_name: str,
    module_in: schemas.ProjectModuleUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_delete_project),
) -> Any:
    """Update project module if current user is project owner."""
    updated_module = crud.project_module.update_project_module(
        db,
        project_id=project_id,
        module_name=module_name,
        enabled=module_in.enabled,
    )
    if not updated_module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project module not found",
        )
    return updated_module
