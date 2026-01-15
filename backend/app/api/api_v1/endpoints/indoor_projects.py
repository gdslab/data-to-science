import logging
from typing import Any, Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

logger = logging.getLogger("__name__")

router = APIRouter()


@router.post(
    "", response_model=schemas.IndoorProject, status_code=status.HTTP_201_CREATED
)
def create_indoor_project(
    indoor_project_in: schemas.IndoorProjectCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create new indoor project for current user.
    """
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot create indoor projects",
        )

    indoor_project = crud.indoor_project.create_with_owner(
        db, obj_in=indoor_project_in, owner_id=current_user.id
    )

    return indoor_project


@router.get("/{indoor_project_id}", response_model=schemas.IndoorProject)
def read_indoor_project(
    indoor_project_id: UUID4,
    indoor_project: models.IndoorProject = Depends(deps.can_read_indoor_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch indoor project if current user is owner, manager, or viewer.
    """
    return indoor_project


@router.get("", response_model=Sequence[schemas.IndoorProject])
def read_indoor_projects(
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all indoor projects owned by current user.
    """
    indoor_projects = crud.indoor_project.read_multi_by_user_id(
        db, user_id=current_user.id
    )

    return indoor_projects


@router.put("/{indoor_project_id}", response_model=schemas.IndoorProject)
def update_indoor_project(
    indoor_project_id: UUID4,
    indoor_project_in: schemas.IndoorProjectUpdate,
    indoor_project: models.IndoorProject = Depends(deps.can_read_write_indoor_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Update indoor project if current user is project owner or manager.
    """
    # Validate date consistency by comparing effective values
    # (new value if provided in update, otherwise existing value)
    effective_start_date = (
        indoor_project_in.start_date
        if indoor_project_in.start_date is not None
        else indoor_project.start_date
    )
    effective_end_date = (
        indoor_project_in.end_date
        if indoor_project_in.end_date is not None
        else indoor_project.end_date
    )

    if effective_start_date and effective_end_date:
        if effective_start_date > effective_end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Start date must be before end date",
            )

    updated_indoor_project = crud.indoor_project.update_indoor_project(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_obj=indoor_project,
        indoor_project_in=indoor_project_in,
        user_id=current_user.id,
    )
    return updated_indoor_project


@router.delete("/{indoor_project_id}", response_model=schemas.IndoorProject)
def deactivate_indoor_project(
    indoor_project_id: UUID4,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Deactivate indoor project if current user is project owner.
    """
    deactivated_indoor_project = crud.indoor_project.deactivate(
        db, indoor_project_id=indoor_project.id
    )
    if not deactivated_indoor_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to deactivate indoor project",
        )
    return deactivated_indoor_project
