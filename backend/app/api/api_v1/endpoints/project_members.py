from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post(
    "", response_model=schemas.ProjectMember, status_code=status.HTTP_201_CREATED
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
    if not project.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
        )
    project_member = crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    if not project_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return project_member


@router.get("", response_model=list[schemas.ProjectMember])
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


@router.delete(
    "/{member_id}",
    response_model=schemas.ProjectMember,
    status_code=status.HTTP_200_OK,
)
def remove_project_member(
    team_id: UUID,
    member_id: UUID,
    project: models.Team = Depends(deps.can_read_write_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Remove project member from project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    if project.owner_id == member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove self (owner) from project",
        )
    removed_project_member = crud.project_member.remove(db, id=member_id)
    return removed_project_member
