from sqlalchemy.orm import Session

from app import crud
from app.models.tag import Tag
from app.schemas.tag import TagCreate


def create_tag(db: Session, name: str = "test-tag") -> Tag:
    """Create a test tag."""
    tag_in = TagCreate(name=name)
    tag = crud.tag.create(db, obj_in=tag_in)
    return tag


def create_tag_in(name: str = "test-tag") -> TagCreate:
    """Create a TagCreate schema for testing."""
    return TagCreate(name=name)
