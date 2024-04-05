from sqlalchemy.orm import Session

from app import crud
from app.schemas.api_key import APIKeyUpdate
from app.tests.utils.user import create_user


def test_create_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    assert api_key
    assert api_key.api_key
    assert api_key.created_at
    assert api_key.is_active
    assert not api_key.last_used_at
    assert api_key.total_requests == 0
    assert api_key.user_id == user.id


def test_create_second_api_key_deactivates_first_api_key(db: Session) -> None:
    user = create_user(db)
    first_api_key = crud.api_key.create_with_user(db, user_id=user.id)
    assert first_api_key
    assert first_api_key.api_key
    assert first_api_key.is_active
    second_api_key = crud.api_key.create_with_user(db, user_id=user.id)
    assert second_api_key
    assert second_api_key.api_key
    assert second_api_key.is_active
    first_api_key_after_second_created = crud.api_key.get(db, id=first_api_key.id)
    assert first_api_key_after_second_created
    assert not first_api_key_after_second_created.is_active


def test_read_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    api_key_in_db = crud.api_key.get_by_user(db, user_id=user.id)
    assert api_key_in_db
    assert api_key_in_db.api_key == api_key.api_key
    assert api_key_in_db.is_active
    assert api_key_in_db.user_id == user.id


def test_update_api_key(db: Session) -> None:
    user = create_user(db)
    crud.api_key.create_with_user(db, user_id=user.id)
    api_key_in_db = crud.api_key.get_by_user(db, user_id=user.id)
    assert api_key_in_db
    assert api_key_in_db.is_active
    # increment total_requests from default 0 value to 1
    api_key_in_update = APIKeyUpdate(total_requests=api_key_in_db.total_requests + 1)
    api_key_updated = crud.api_key.update(
        db, db_obj=api_key_in_db, obj_in=api_key_in_update
    )
    assert api_key_updated.total_requests == 1


def test_deactivate_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    api_key_in_db = crud.api_key.get_by_user(db, user_id=user.id)
    api_key_removed = crud.api_key.deactivate(db, user_id=user.id)
    api_key_in_db_after_deactivation = crud.api_key.get_by_user(db, user_id=user.id)
    assert api_key_in_db_after_deactivation is None
    assert api_key_removed
    assert api_key_removed.id == api_key_in_db.id
    assert api_key_removed.api_key == api_key_in_db.api_key
    assert not api_key_removed.is_active
