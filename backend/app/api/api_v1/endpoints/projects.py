from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import create_project_field_preview


router = APIRouter()


@router.post("", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    request: Request,
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new project for current user."""
    project = crud.project.create_with_owner(
        db, obj_in=project_in, owner_id=current_user.id
    )
    # Create preview image for project field boundary
    project_in_db = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project.id
    )
    if project_in_db["response_code"] == status.HTTP_200_OK:
        coordinates = project_in_db["result"].field["geometry"]["coordinates"]
        create_project_field_preview(request, project.id, coordinates)
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    project_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    """Retrieve project by id."""
    return project


@router.get("", response_model=list[schemas.Project])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of projects current user belongs to."""
    projects = crud.project.get_user_project_list(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return projects


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: UUID,
    project_in: schemas.ProjectUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update project if current user is project owner or member."""
    project = crud.project.update(db, db_obj=project, obj_in=project_in)
    return project


@router.delete("/{project_id}", response_model=schemas.Project)
def deactivate_project(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    deactivated_project = crud.project.deactivate(db, project_id=project.id)
    if not deactivated_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to deactivate"
        )
    return deactivated_project
