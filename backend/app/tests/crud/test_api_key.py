from sqlalchemy.orm import Session

from app import crud
from app.models.enums.api_key_scope import ALL_API_KEY_SCOPES, APIKeyScope
from app.schemas.api_key import APIKeyUpdate, APIKeyUpdateRequest
from app.tests.utils.user import create_user


def test_create_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.READ], name="qgis"
    )
    assert api_key
    assert api_key.api_key
    assert api_key.created_at
    assert api_key.is_active
    assert not api_key.last_used_at
    assert api_key.name == "qgis"
    assert api_key.scopes == ["read"]
    assert api_key.total_requests == 0
    assert api_key.user_id == user.id


def test_create_second_api_key_keeps_first_api_key_active(db: Session) -> None:
    user = create_user(db)
    first_api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    second_api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.CREATE]
    )
    assert second_api_key.is_active
    assert second_api_key.api_key != first_api_key.api_key
    first_api_key_after_second_created = crud.api_key.get(db, id=first_api_key.id)
    assert first_api_key_after_second_created
    assert first_api_key_after_second_created.is_active


def test_has_scope(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.CREATE]
    )
    assert api_key.has_scope(APIKeyScope.CREATE)
    assert not api_key.has_scope(APIKeyScope.READ)
    assert not api_key.has_scope(APIKeyScope.UPDATE)
    assert not api_key.has_scope(APIKeyScope.DELETE)


def test_read_api_keys_by_user(db: Session) -> None:
    user = create_user(db)
    other_user = create_user(db)
    first_api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    second_api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    revoked_api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    crud.api_key.deactivate(db, api_key_id=revoked_api_key.id, user_id=user.id)
    crud.api_key.create_with_user(db, user_id=other_user.id, scopes=ALL_API_KEY_SCOPES)
    api_keys = crud.api_key.get_multi_by_user(db, user_id=user.id)
    assert [api_key.id for api_key in api_keys] == [
        first_api_key.id,
        second_api_key.id,
    ]
    assert crud.api_key.count_active_by_user(db, user_id=user.id) == 2


def test_read_api_key_by_id_and_user(db: Session) -> None:
    user = create_user(db)
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    api_key_in_db = crud.api_key.get_active_by_id_and_user(
        db, api_key_id=api_key.id, user_id=user.id
    )
    assert api_key_in_db
    assert api_key_in_db.id == api_key.id
    assert (
        crud.api_key.get_active_by_id_and_user(
            db, api_key_id=api_key.id, user_id=other_user.id
        )
        is None
    )


def test_update_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    # increment total_requests from default 0 value to 1
    api_key_in_update = APIKeyUpdate(total_requests=api_key.total_requests + 1)
    api_key_updated = crud.api_key.update(db, db_obj=api_key, obj_in=api_key_in_update)
    assert api_key_updated.total_requests == 1


def test_record_api_key_use(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    assert api_key.last_used_at is None
    assert api_key.total_requests == 0
    first_use = crud.api_key.record_use(db, api_key)
    assert first_use.last_used_at
    assert first_use.total_requests == 1
    second_use = crud.api_key.record_use(db, first_use)
    assert second_use.last_used_at >= first_use.last_used_at
    assert second_use.total_requests == 2


def test_update_api_key_name_and_scopes_by_user(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.READ]
    )
    api_key_updated = crud.api_key.update_by_user(
        db,
        api_key_id=api_key.id,
        user_id=user.id,
        obj_in=APIKeyUpdateRequest(
            name="device", scopes=[APIKeyScope.CREATE, APIKeyScope.UPDATE]
        ),
    )
    assert api_key_updated
    assert api_key_updated.name == "device"
    assert api_key_updated.scopes == ["create", "update"]


def test_update_api_key_name_only_keeps_scopes(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.READ]
    )
    api_key_updated = crud.api_key.update_by_user(
        db,
        api_key_id=api_key.id,
        user_id=user.id,
        obj_in=APIKeyUpdateRequest(name="renamed"),
    )
    assert api_key_updated
    assert api_key_updated.name == "renamed"
    assert api_key_updated.scopes == ["read"]


def test_update_api_key_owned_by_other_user(db: Session) -> None:
    user = create_user(db)
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.READ]
    )
    api_key_updated = crud.api_key.update_by_user(
        db,
        api_key_id=api_key.id,
        user_id=other_user.id,
        obj_in=APIKeyUpdateRequest(scopes=ALL_API_KEY_SCOPES),
    )
    assert api_key_updated is None
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert api_key_in_db.scopes == ["read"]


def test_deactivate_api_key(db: Session) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    api_key_removed = crud.api_key.deactivate(
        db, api_key_id=api_key.id, user_id=user.id
    )
    assert api_key_removed
    assert api_key_removed.id == api_key.id
    assert not api_key_removed.is_active
    assert api_key_removed.deactivated_at
    assert crud.api_key.get_multi_by_user(db, user_id=user.id) == []


def test_deactivate_api_key_owned_by_other_user(db: Session) -> None:
    user = create_user(db)
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=ALL_API_KEY_SCOPES
    )
    assert (
        crud.api_key.deactivate(db, api_key_id=api_key.id, user_id=other_user.id)
        is None
    )
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert api_key_in_db.is_active
