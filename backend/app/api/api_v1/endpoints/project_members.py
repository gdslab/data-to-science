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
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    project_member = crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    if not project_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return project_member


@router.post(
    "/multi",
    response_model=list[schemas.ProjectMember],
    status_code=status.HTTP_201_CREATED,
)
def create_project_members(
    project_id: UUID,
    project_members: list[UUID],
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    project_members = crud.project_member.create_multi_with_project(
        db, member_ids=project_members, project_id=project.id
    )
    return project_members


@router.get("/{project_member_id}", response_model=schemas.ProjectMember)
def read_project_member(
    project_member_id: UUID,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_id=project.id, member_id=project_member_id
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
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    project_members = crud.project_member.get_list_of_project_members(
        db, project_id=project.id, skip=skip, limit=limit
    )
    return project_members


@router.put("/{project_member_id}", response_model=schemas.ProjectMember)
def update_project_member(
    project_member_id: UUID,
    project_member_in: schemas.ProjectMemberUpdate,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    project_member_db = crud.project_member.get(db, id=project_member_id)
    if not project_member_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    updated_project_member = crud.project_member.update_project_member(
        db, project_member_obj=project_member_db, project_member_in=project_member_in
    )
    if updated_project_member["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=updated_project_member["response_code"],
            detail=updated_project_member["message"],
        )
    return updated_project_member["result"]


@router.delete("/{project_member_id}", response_model=schemas.ProjectMember)
def remove_project_member(
    project_member_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    project_member = crud.project_member.get(db, id=project_member_id)
    if not project_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    if project_member.member_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project creator cannot be removed",
        )
    removed_project_member = crud.project_member.remove(db, id=project_member_id)
    return removed_project_member
