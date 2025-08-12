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
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch indoor project owned by current user.
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
