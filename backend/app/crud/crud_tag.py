from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.tag import Tag
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
)


class CRUDTag(CRUDBase[Tag, TagCreate, TagUpdate]):
    def get_by_name(self, db: Session, name: str) -> Optional[Tag]:
        """Get tag by name."""
        with db as session:
            statement = select(Tag).where(Tag.name == name)
            return session.scalar(statement)

    def get_or_create(self, db: Session, *, obj_in: TagCreate) -> Tag:
        """
        Get existing tag by name or create a new one.
        Handles unique constraint violations gracefully.
        """
        try:
            # Try to create the tag
            return self.create(db, obj_in=obj_in)
        except IntegrityError:
            # Tag with this name already exists, fetch and return it
            db.rollback()
            existing_tag = self.get_by_name(db, name=obj_in.name)
            if existing_tag:
                return existing_tag
            # This shouldn't happen, but if it does, re-raise the error
            raise


tag = CRUDTag(Tag)
