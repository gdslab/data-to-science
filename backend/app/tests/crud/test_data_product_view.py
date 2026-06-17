from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_view import create_data_product_view
from app.tests.utils.user import create_user


def test_first_view_creates_row(db: Session) -> None:
    sample = SampleDataProduct(db)
    user_id = sample.user.id

    view = crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, user_id=user_id
    )

    assert view is not None
    assert view.data_product_id == sample.obj.id
    assert view.user_id == user_id


def test_dedup_within_window_returns_none(db: Session) -> None:
    sample = SampleDataProduct(db)

    crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )
    result = crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )

    assert result is None


def test_view_after_window_creates_new_row(db: Session) -> None:
    sample = SampleDataProduct(db)
    old_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)

    # Plant a backdated row
    create_data_product_view(
        db, data_product_id=sample.obj.id, user_id=sample.user.id, viewed_at=old_time
    )

    # New view should succeed (window_hours=0.5h, but first row is 2h old)
    view = crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )

    assert view is not None


def test_anonymous_session_and_user_are_independent(db: Session) -> None:
    sample = SampleDataProduct(db)

    user_view = crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )
    session_view = crud.data_product_view.create_if_not_recent(
        db, data_product_id=sample.obj.id, session_id="test-session-abc"
    )

    assert user_view is not None
    assert session_view is not None


def test_missing_both_identities_raises_value_error(db: Session) -> None:
    sample = SampleDataProduct(db)

    with pytest.raises(ValueError):
        crud.data_product_view.create_if_not_recent(
            db, data_product_id=sample.obj.id
        )


def test_get_count_by_data_product_id(db: Session) -> None:
    sample = SampleDataProduct(db)
    other_user = create_user(db)

    create_data_product_view(db, data_product_id=sample.obj.id, user_id=sample.user.id)
    create_data_product_view(db, data_product_id=sample.obj.id, user_id=other_user.id)
    create_data_product_view(db, data_product_id=sample.obj.id, session_id="anon-1")

    count = crud.data_product_view.get_count_by_data_product_id(
        db, data_product_id=sample.obj.id
    )
    assert count == 3


def test_get_count_is_zero_for_no_views(db: Session) -> None:
    sample = SampleDataProduct(db)

    count = crud.data_product_view.get_count_by_data_product_id(
        db, data_product_id=sample.obj.id
    )
    assert count == 0
