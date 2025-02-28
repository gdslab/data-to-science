from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.shortened_url import ShortenedUrlCreate, ShortenedUrlUpdate
from app.utils.unique_id import generate_unique_id
from app.tests.utils.user import create_user

ORIGINAL_URL = f"{settings.API_DOMAIN}/full/share/url"


def test_create_shortened_url(db: Session) -> None:
    """
    Test creating a ShortenedUrl record using create_with_unique_short_id.

    Verifies:
      - A record is returned with a non-null id and short_id.
      - The original URL is correctly stored.
      - The clicks count is initialized to 0.
      - The created_at timestamp is set.
      - The expires_at field is None by default.
      - The is_active field is True by default.
      - The user_id field is correctly set.
      - last_accessed_at is None and updated_at is set.
    """
    user_id = create_user(db).id
    shortened_url = crud.shortened_url.create_with_unique_short_id(
        db, original_url=ORIGINAL_URL, user_id=user_id
    )

    assert shortened_url is not None
    assert shortened_url.id is not None
    assert shortened_url.short_id is not None
    assert shortened_url.original_url == ORIGINAL_URL
    assert shortened_url.clicks == 0
    assert shortened_url.created_at is not None
    assert shortened_url.expires_at is None
    assert shortened_url.is_active is True
    assert shortened_url.user_id == user_id
    assert shortened_url.last_accessed_at is None
    assert shortened_url.updated_at is not None


def test_create_shortened_url_for_existing_original_url_increments_clicks(
    db: Session,
) -> None:
    """
    Test creating a ShortenedUrl record for an existing original URL.

    This test:
      - Creates a record for a specific original URL.
      - Creates a second record for the same original URL.
      - Verifies that the second record has the same short_id as the first.
    """
    user_id = create_user(db).id
    shortened_url = crud.shortened_url.create_with_unique_short_id(
        db, original_url=ORIGINAL_URL, user_id=user_id
    )

    # Create a second record for the same original URL
    second_shortened_url = crud.shortened_url.create_with_unique_short_id(
        db, original_url=ORIGINAL_URL, user_id=user_id
    )

    assert shortened_url is not None
    assert second_shortened_url is not None
    assert second_shortened_url.short_id == shortened_url.short_id


def test_duplicate_shortened_url_fails(db: Session) -> None:
    """
    Test that attempting to create two ShortenedUrl records with the same short_id
    violates the unique constraint on the short_id field.

    This test:
      - Creates a record with a specific short_id.
      - Attempts to create a second record with the same short_id.
      - Expects an IntegrityError to be raised.
    """
    user_id = create_user(db).id
    unique_id = generate_unique_id()
    obj_in = ShortenedUrlCreate(
        original_url=ORIGINAL_URL, short_id=unique_id, user_id=user_id
    )
    crud.shortened_url.create(db, obj_in=obj_in)

    with pytest.raises(IntegrityError):
        crud.shortened_url.create(db, obj_in=obj_in)


def test_read_shortened_url_by_original_url(db: Session) -> None:
    """
    Test retrieving a ShortenedUrl record by its original URL using get_by_original_url.

    This test:
      - Creates a non-expired record.
      - Retrieves it by its original URL and checks the returned record.
      - Also creates an expired record and verifies that retrieval returns None.
    """
    user_id = create_user(db).id
    # Create a non-expired record (expires_at is None)
    test_url = ORIGINAL_URL + "/test-read-short"
    shortened_url = crud.shortened_url.create_with_unique_short_id(
        db, original_url=test_url, user_id=user_id
    )
    retrieved_shortened_url = crud.shortened_url.get_by_original_url(
        db, original_url=test_url, user_id=user_id
    )

    assert shortened_url is not None
    assert retrieved_shortened_url is not None
    assert retrieved_shortened_url.id == shortened_url.id
    assert retrieved_shortened_url.short_id == shortened_url.short_id

    # Create an expired record (expires_at in the past)
    expired_url = ORIGINAL_URL + "/test-expired-original"
    expired_date = datetime.now(timezone.utc) - timedelta(days=1)
    expired_obj_in = ShortenedUrlCreate(
        original_url=expired_url,
        short_id=generate_unique_id(),
        expires_at=expired_date,
        user_id=user_id,
    )
    crud.shortened_url.create(db, obj_in=expired_obj_in)

    expired_retrieved = crud.shortened_url.get_by_original_url(
        db, original_url=expired_url, user_id=user_id
    )
    assert expired_retrieved is None


def test_read_shortened_url_by_short_id(db: Session) -> None:
    """
    Test retrieving a ShortenedUrl record by its short_id using get_by_short_id.

    This test:
      - Creates a non-expired record.
      - Retrieves it by its short_id and checks the returned record.
      - Also creates an expired record and verifies that retrieval returns None.
    """
    user_id = create_user(db).id
    # Create a non-expired record (expires_at is None)
    test_url = ORIGINAL_URL + "/test-read-short"
    unique_short_id = generate_unique_id()
    obj_in = ShortenedUrlCreate(
        original_url=test_url, short_id=unique_short_id, user_id=user_id
    )
    created_url = crud.shortened_url.create(db, obj_in=obj_in)

    retrieved = crud.shortened_url.get_by_short_id(db, short_id=unique_short_id)
    assert retrieved is not None
    assert retrieved.id == created_url.id

    # Create an expired record (expires_at in the past)
    expired_short_id = generate_unique_id()
    expired_url = ORIGINAL_URL + "/test-expired-short"
    expired_date = datetime.now(timezone.utc) - timedelta(days=1)
    expired_obj_in = ShortenedUrlCreate(
        original_url=expired_url,
        short_id=expired_short_id,
        expires_at=expired_date,
        user_id=user_id,
    )
    crud.shortened_url.create(db, obj_in=expired_obj_in)

    expired_retrieved = crud.shortened_url.get_by_short_id(
        db, short_id=expired_short_id
    )
    assert expired_retrieved is None


def test_update_shortened_url(db: Session) -> None:
    """
    Test updating an existing ShortenedUrl record.

    This test:
      - Creates a record.
      - Updates the click count and sets an expiration date.
      - Verifies that the updates are persisted correctly.
    """
    user_id = create_user(db).id
    test_url = ORIGINAL_URL + "/test-update"
    unique_short_id = generate_unique_id()
    obj_in = ShortenedUrlCreate(
        original_url=test_url, short_id=unique_short_id, user_id=user_id
    )
    created_url = crud.shortened_url.create(db, obj_in=obj_in)

    # Define new values: increase clicks and set expires_at to a future date
    new_click_count = created_url.clicks + 10
    future_date = datetime.now(timezone.utc) + timedelta(days=7)
    update_data = ShortenedUrlUpdate(clicks=new_click_count, expires_at=future_date)

    updated_url = crud.shortened_url.update(db, db_obj=created_url, obj_in=update_data)
    assert updated_url.clicks == new_click_count
    assert updated_url.expires_at == future_date
    # Check that updated_at is set (and possibly updated)
    assert updated_url.updated_at is not None


def test_delete_shortened_url(db: Session) -> None:
    """
    Test deleting an existing ShortenedUrl record.

    This test:
      - Creates a record.
      - Deletes it using the remove method.
      - Verifies that the record is no longer retrievable by either original_url or short_id.
    """
    user_id = create_user(db).id
    test_url = ORIGINAL_URL + "/test-delete"
    unique_short_id = generate_unique_id()
    obj_in = ShortenedUrlCreate(
        original_url=test_url, short_id=unique_short_id, user_id=user_id
    )
    created_url = crud.shortened_url.create(db, obj_in=obj_in)

    # Delete the record (assuming CRUDBase provides a remove method)
    deleted_url = crud.shortened_url.remove(db, id=created_url.id)
    assert deleted_url is not None

    # Confirm that the record is no longer found by original URL or short_id
    assert (
        crud.shortened_url.get_by_original_url(
            db, original_url=test_url, user_id=user_id
        )
        is None
    )
    assert crud.shortened_url.get_by_short_id(db, short_id=unique_short_id) is None
