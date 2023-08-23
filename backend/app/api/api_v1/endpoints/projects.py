from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
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
    project_id: UUID,
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


@router.get("/{project_id}/members", response_model=list[schemas.ProjectMember])
def read_project_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project),
) -> Any:
    """Retrieve members of a project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id, skip=skip, limit=limit
    )
    return project_members


@router.put("/{project_id}")
def update_project(
    project_id: UUID,
    project_in: schemas.ProjectUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
):
    """Update project if current user is project owner or member."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project = crud.project.update(db, db_obj=project, obj_in=project_in)
    return project


@router.post(
    "/{project_id}/members",
    response_model=schemas.ProjectMember,
    status_code=status.HTTP_201_CREATED,
)
def create_project_member(
    project_id: UUID,
    project_member_in: schemas.ProjectMemberCreate,
    project: models.Project = Depends(deps.can_read_write_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Add project member to project if current user is team owner."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project_member = crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    if not project_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return project_member
