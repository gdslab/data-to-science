from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new project for current user."""
    project = crud.project.create_with_owner(
        db, obj_in=project_in, owner_id=current_user.id
    )
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    project_id: str,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project),
) -> Any:
    """Retrieve project by id."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )
    return project


@router.get("/", response_model=list[schemas.Project])
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


@router.put("/{project_id}")
def update_project(
    project_id: str,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
):
    pass
    # does current user have permission to update this project id?
    # yes if:
    # 1) owns the project
    # 2)
