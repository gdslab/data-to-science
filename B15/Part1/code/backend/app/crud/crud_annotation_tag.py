from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import crud
from app.crud.base import CRUDBase
from app.models.annotation_tag import AnnotationTag
from app.schemas.annotation_tag import AnnotationTagCreate, AnnotationTagUpdate
from app.schemas.tag import TagCreate


class CRUDAnnotationTag(
    CRUDBase[AnnotationTag, AnnotationTagCreate, AnnotationTagUpdate]
):
    def create_with_annotation(
        self, db: Session, *, obj_in: AnnotationTagCreate, annotation_id: UUID
    ) -> AnnotationTag:
        """Create an annotation-tag relation with automatic tag creation.

        Automatically creates the tag if it doesn't exist using get_or_create.
        The provided annotation_id argument takes precedence over any value in obj_in.
        """
        # Get or create the tag
        tag = crud.tag.get_or_create(db, obj_in=TagCreate(name=obj_in.tag))

        # Create the annotation_tag with the tag_id
        db_obj = AnnotationTag(annotation_id=annotation_id, tag_id=tag.id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)

            # Eagerly load the tag relationship before returning
            statement = (
                select(AnnotationTag)
                .options(selectinload(AnnotationTag.tag))
                .where(AnnotationTag.id == db_obj.id)
            )
            result = session.scalar(statement)
            if result is None:
                raise RuntimeError(
                    f"AnnotationTag {db_obj.id} not found after creation"
                )
            db_obj = result
        return db_obj

    def get_multi_by_annotation_id(
        self, db: Session, annotation_id: UUID
    ) -> Sequence[AnnotationTag]:
        """Return all annotation-tag rows for a given annotation with tags loaded."""
        statement = (
            select(AnnotationTag)
            .options(selectinload(AnnotationTag.tag))
            .where(AnnotationTag.annotation_id == annotation_id)
        )
        with db as session:
            return session.scalars(statement).all()


annotation_tag = CRUDAnnotationTag(AnnotationTag)
