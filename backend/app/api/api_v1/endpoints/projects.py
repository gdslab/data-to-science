import logging
from typing import Any, List
from uuid import UUID

from geojson_pydantic import Feature
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import create_project_field_preview


logger = logging.getLogger("__name__")

router = APIRouter()


@router.post("", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new project for current user."""
    try:
        project = crud.project.create_with_owner(
            db,
            obj_in=project_in,
            owner_id=current_user.id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create project",
        )
    if project["response_code"] != status.HTTP_201_CREATED:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    if not project["result"].id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create project",
        )
    # Create preview image for project field boundary
    project_in_db = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project["result"].id
    )
    if project_in_db["result"]:
        coordinates = project_in_db["result"].field["geometry"]["coordinates"]
        features = [Feature(**project_in_db["result"].field)]
        try:
            create_project_field_preview(project["result"].id, features)
        except Exception:
            logger.exception("Unable to create preview map")
    return project["result"]


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    project_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    """Retrieve project by id."""
    return project


@router.get("", response_model=List[schemas.project.Projects])
def read_projects(
    edit_only: bool = False,
    has_raster: bool = False,
    include_all: bool = False,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of projects current user belongs to."""
    projects = crud.project.get_user_projects(
        db,
        user=current_user,
        has_raster=has_raster,
        include_all=include_all,
    )
    return projects


@router.get("/landing/", response_model=List[schemas.project.Projects])
def read_projects2(
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    projects = crud.project.get_user_projects(db, user_id=current_user.id)
    return projects


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: UUID,
    project_in: schemas.ProjectUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update project if current user is project owner or member."""
    project = crud.project.update_project(
        db,
        project_id=project_id,
        project_obj=project,
        project_in=project_in,
        user_id=current_user.id,
    )
    if project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    return project["result"]


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
