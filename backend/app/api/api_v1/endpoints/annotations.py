import logging
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.models.data_product import DataProduct
from app.models.enums.visibility import Visibility
from app.models.user import User
from app.schemas.annotation import Annotation, AnnotationCreate, AnnotationUpdate
from app.schemas.project import Project
from app.schemas.role import Role

router = APIRouter()

logger = logging.getLogger("__name__")


@router.post("", response_model=Annotation, status_code=status.HTTP_201_CREATED)
def create_annotation(
    annotation_in: AnnotationCreate,
    data_product_id: UUID,
    current_user: User = Depends(deps.get_current_approved_user),
    data_product: DataProduct = Depends(deps.can_read_data_product),
    project: Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create annotation for a data product.

    Viewers can only create personal (OWNER) annotations.
    PROJECT-level annotations require manager or owner role.
    """
    if annotation_in.visibility == Visibility.PROJECT and project.role not in (
        Role.OWNER,
        Role.MANAGER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and owners can create project-level annotations",
        )
    try:
        annotation = crud.annotation.create_with_data_product(
            db=db,
            obj_in=annotation_in,
            data_product_id=data_product.id,
            created_by_id=current_user.id,
        )
    except Exception:
        logger.exception(
            f"Failed to create annotation for data product {data_product_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create annotation",
        )
    return annotation


@router.get(
    "/{annotation_id}", response_model=Annotation, status_code=status.HTTP_200_OK
)
def get_annotation_by_id(
    annotation_id: UUID,
    data_product: DataProduct = Depends(deps.can_read_data_product),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get annotation by ID."""
    annotation = crud.annotation.get_with_created_by(db=db, id=annotation_id)
    if annotation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )
    if annotation.data_product_id != data_product.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Annotation does not belong to specified data product",
        )
    return annotation


@router.get("", response_model=List[Annotation], status_code=status.HTTP_200_OK)
def get_annotations(
    current_user: User = Depends(deps.get_current_approved_user),
    data_product: DataProduct = Depends(deps.can_read_data_product),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get annotations for a data product."""
    annotations = crud.annotation.get_multi_by_data_product_id(
        db=db, data_product_id=data_product.id, user_id=current_user.id
    )
    return annotations


@router.put(
    "/{annotation_id}", response_model=Annotation, status_code=status.HTTP_200_OK
)
def update_annotation(
    annotation_id: UUID,
    annotation_in: AnnotationUpdate,
    data_product: DataProduct = Depends(deps.can_read_write_data_product),
    db: Session = Depends(deps.get_db),
) -> Any:
    annotation = crud.annotation.get_with_created_by(db=db, id=annotation_id)
    if annotation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )
    if annotation.data_product_id != data_product.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Annotation does not belong to specified project",
        )
    try:
        updated_annotation = crud.annotation.update(
            db=db, db_obj=annotation, obj_in=annotation_in
        )
    except Exception:
        logger.exception(f"Failed to update annotation {annotation_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update annotation",
        )
    return updated_annotation


@router.delete(
    "/{annotation_id}", response_model=Annotation, status_code=status.HTTP_200_OK
)
def delete_annotation(
    annotation_id: UUID,
    current_user: User = Depends(deps.get_current_approved_user),
    data_product: DataProduct = Depends(deps.can_read_write_data_product),
    project: Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Delete an annotation.

    Personal (OWNER visibility) annotations can only be deleted by their creator.
    Shared (PROJECT visibility) annotations can be deleted by their creator or
    any project owner.
    """
    annotation = crud.annotation.get_with_created_by(db=db, id=annotation_id)
    if annotation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )
    if annotation.data_product_id != data_product.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Annotation does not belong to specified data product",
        )

    is_creator = annotation.created_by_id == current_user.id
    is_project_owner = project.role == Role.OWNER

    if annotation.visibility == Visibility.OWNER:
        if not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator can delete personal annotations",
            )
    else:
        if not is_creator and not is_project_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator or a project owner can delete shared annotations",
            )

    try:
        deleted_annotation = crud.annotation.remove(db=db, id=annotation_id)
    except Exception:
        logger.exception(f"Failed to delete annotation {annotation_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete annotation",
        )
    return deleted_annotation
