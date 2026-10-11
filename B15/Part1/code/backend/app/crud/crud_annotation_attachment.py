from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.annotation_attachment import AnnotationAttachment
from app.schemas.annotation_attachment import (
    AnnotationAttachmentCreate,
    AnnotationAttachmentUpdate,
)


class CRUDAnnotationAttachment(
    CRUDBase[
        AnnotationAttachment, AnnotationAttachmentCreate, AnnotationAttachmentUpdate
    ]
):
    def create_with_annotation(
        self, db: Session, *, obj_in: AnnotationAttachmentCreate, annotation_id: UUID
    ) -> AnnotationAttachment:
        """Create an annotation attachment with annotation_id passed separately."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = AnnotationAttachment(**obj_in_data, annotation_id=annotation_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_multi_by_annotation_id(
        self, db: Session, annotation_id: UUID
    ) -> Sequence[AnnotationAttachment]:
        statement = select(AnnotationAttachment).where(
            AnnotationAttachment.annotation_id == annotation_id
        )
        with db as session:
            return session.scalars(statement).all()


annotation_attachment = CRUDAnnotationAttachment(AnnotationAttachment)
