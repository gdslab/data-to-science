import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.tag import TagCreate, TagUpdate
from app.tests.utils.tag import create_tag


def test_create_tag(db: Session) -> None:
    """Verify new tag is created in database."""
    tag_name = "test-tag"
    tag_in = TagCreate(name=tag_name)
    tag = crud.tag.create(db, obj_in=tag_in)
    assert tag
    assert tag.id
    assert tag.name == tag_name
    assert tag.created_at is not None
    assert tag.updated_at is not None


def test_create_duplicate_tag(db: Session) -> None:
    """Verify cannot create new tag with an existing (non-unique) name."""
    tag_name = "duplicate-tag"
    tag_in = TagCreate(name=tag_name)
    crud.tag.create(db, obj_in=tag_in)
    # Unique constraint should cause creation of duplicate tag to fail
    with pytest.raises(IntegrityError):
        crud.tag.create(db, obj_in=tag_in)


def test_get_or_create_existing_tag(db: Session) -> None:
    """Verify get_or_create returns existing tag when name already exists."""
    tag_name = "existing-tag"
    # Create initial tag
    tag_in = TagCreate(name=tag_name)
    original_tag = crud.tag.create(db, obj_in=tag_in)

    # Try to get_or_create with same name
    retrieved_tag = crud.tag.get_or_create(db, obj_in=tag_in)
    assert retrieved_tag
    assert retrieved_tag.id == original_tag.id
    assert retrieved_tag.name == tag_name


def test_get_or_create_new_tag(db: Session) -> None:
    """Verify get_or_create creates new tag when name doesn't exist."""
    tag_name = "new-tag"
    tag_in = TagCreate(name=tag_name)
    tag = crud.tag.get_or_create(db, obj_in=tag_in)
    assert tag
    assert tag.id
    assert tag.name == tag_name
    assert tag.created_at is not None
    assert tag.updated_at is not None


def test_get_tag_by_id(db: Session) -> None:
    """Verify retrieving tag by id returns correct tag."""
    tag = create_tag(db, name="test-get-by-id")
    retrieved_tag = crud.tag.get(db, id=tag.id)
    assert retrieved_tag
    assert retrieved_tag.id == tag.id
    assert retrieved_tag.name == tag.name


def test_get_tag_by_name(db: Session) -> None:
    """Verify retrieving tag by name returns correct tag."""
    tag_name = "test-get-by-name"
    tag = create_tag(db, name=tag_name)
    retrieved_tag = crud.tag.get_by_name(db, name=tag_name)
    assert retrieved_tag
    assert retrieved_tag.id == tag.id
    assert retrieved_tag.name == tag_name


def test_get_tag_by_nonexistent_name(db: Session) -> None:
    """Verify retrieving tag by nonexistent name returns None."""
    retrieved_tag = crud.tag.get_by_name(db, name="nonexistent-tag")
    assert retrieved_tag is None


def test_get_multiple_tags(db: Session) -> None:
    """Verify retrieving multiple tags."""
    tag1 = create_tag(db, name="tag-1")
    tag2 = create_tag(db, name="tag-2")
    tag3 = create_tag(db, name="tag-3")

    tags = crud.tag.get_multi(db, skip=0, limit=10)
    assert tags
    assert len(tags) >= 3  # May have other tags from other tests
    tag_ids = [tag.id for tag in tags]
    assert tag1.id in tag_ids
    assert tag2.id in tag_ids
    assert tag3.id in tag_ids


def test_update_tag(db: Session) -> None:
    """Verify update changes tag attributes in database."""
    tag = create_tag(db, name="original-tag")
    original_updated_at = tag.updated_at
    new_name = "updated-tag"
    tag_update = TagUpdate(name=new_name)
    updated_tag = crud.tag.update(db, db_obj=tag, obj_in=tag_update)
    assert updated_tag
    assert updated_tag.id == tag.id
    assert updated_tag.name == new_name
    assert updated_tag.updated_at > original_updated_at


def test_delete_tag(db: Session) -> None:
    """Verify tag is removed from database."""
    tag = create_tag(db, name="tag-to-delete")
    deleted_tag = crud.tag.remove(db, id=tag.id)
    assert deleted_tag
    assert deleted_tag.id == tag.id

    # Verify tag is no longer retrievable
    retrieved_tag = crud.tag.get(db, id=tag.id)
    assert retrieved_tag is None
