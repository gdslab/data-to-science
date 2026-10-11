import logging
import os
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core.files import get_absolute_filepath
from app.models.annotation_attachment import AnnotationAttachment
from app.models.data_product import DataProduct
from app.models.user import User
from app.schemas.annotation_attachment import (
    AnnotationAttachment as AnnotationAttachmentSchema,
)

router = APIRouter()

logger = logging.getLogger("__name__")


def _get_verified_attachment(
    db: Session,
    annotation_id: UUID,
    attachment_id: UUID,
    data_product: DataProduct,
) -> AnnotationAttachment:
    """Look up an attachment and verify it belongs to the annotation and data product."""
    annotation = crud.annotation.get(db, id=annotation_id)
    if not annotation or annotation.data_product_id != data_product.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found or does not belong to this data product",
        )

    attachment = crud.annotation_attachment.get(db, id=attachment_id)
    if not attachment or attachment.annotation_id != annotation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found or does not belong to this annotation",
        )
    return attachment


@router.get("/{attachment_id}/download")
def download_annotation_attachment(
    annotation_id: UUID,
    attachment_id: UUID,
    data_product: DataProduct = Depends(deps.can_read_data_product),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Download an annotation attachment by ID."""
    attachment = _get_verified_attachment(
        db, annotation_id, attachment_id, data_product
    )

    abs_path = get_absolute_filepath(attachment.filepath)
    if not os.path.exists(abs_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file not found on disk",
        )

    return FileResponse(
        abs_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/{attachment_id}",
    response_model=AnnotationAttachmentSchema,
    status_code=status.HTTP_200_OK,
)
def delete_annotation_attachment(
    annotation_id: UUID,
    attachment_id: UUID,
    current_user: User = Depends(deps.get_current_approved_user),
    data_product: DataProduct = Depends(deps.can_read_write_data_product),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Delete an annotation attachment by ID."""
    attachment = _get_verified_attachment(
        db, annotation_id, attachment_id, data_product
    )

    # Delete file from disk
    if attachment.filepath:
        abs_path = get_absolute_filepath(attachment.filepath)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    # Delete DB record
    try:
        deleted = crud.annotation_attachment.remove(db, id=attachment_id)
    except Exception:
        logger.exception(f"Failed to delete attachment {attachment_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete attachment",
        )

    return deleted
