from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.put("", response_model=schemas.FilePermission)
def update_file_permission(
    data_product_id: UUID,
    file_permission_in: schemas.FilePermissionUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: schemas.Project = Depends(deps.can_read_write_delete_project),
    flight: models.Flight = Depends(deps.can_read_write_delete_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Check if trying to make file private when project is published
    if (
        project.is_published
        and file_permission_in.is_public is not None
        and file_permission_in.is_public is False
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot make file private when project is published in a STAC catalog",
        )

    current_file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product_id
    )
    if not current_file_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File permission not found"
        )
    updated_file_permission = crud.file_permission.update(
        db, db_obj=current_file_permission, obj_in=file_permission_in
    )
    return updated_file_permission
