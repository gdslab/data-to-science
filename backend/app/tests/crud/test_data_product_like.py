import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.user import create_user


def test_create_and_get_by_data_product_id_and_user_id(db: Session) -> None:
    sample = SampleDataProduct(db)
    user_id = sample.user.id
    data_product_id = sample.obj.id

    like = create_data_product_like(db, data_product_id=data_product_id, user_id=user_id)

    like_in_db = crud.data_product_like.get_by_data_product_id_and_user_id(
        db, data_product_id=data_product_id, user_id=user_id
    )

    assert like_in_db is not None
    assert like_in_db.id == like.id
    assert like_in_db.data_product_id == data_product_id
    assert like_in_db.user_id == user_id


def test_duplicate_like_raises_integrity_error(db: Session) -> None:
    sample = SampleDataProduct(db)
    data_product_id = sample.obj.id
    user_id = sample.user.id

    crud.data_product_like.create(
        db,
        obj_in=schemas.DataProductLikeCreate(
            data_product_id=data_product_id, user_id=user_id
        ),
    )
    with pytest.raises(IntegrityError):
        crud.data_product_like.create(
            db,
            obj_in=schemas.DataProductLikeCreate(
                data_product_id=data_product_id, user_id=user_id
            ),
        )


def test_get_returns_none_for_inactive_data_product(db: Session) -> None:
    sample = SampleDataProduct(db)
    data_product_id = sample.obj.id
    user_id = sample.user.id

    create_data_product_like(db, data_product_id=data_product_id, user_id=user_id)

    crud.data_product.deactivate(db, data_product_id=data_product_id)

    like_in_db = crud.data_product_like.get_by_data_product_id_and_user_id(
        db, data_product_id=data_product_id, user_id=user_id
    )
    assert like_in_db is None


def test_remove_like(db: Session) -> None:
    sample = SampleDataProduct(db)
    like = create_data_product_like(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )

    crud.data_product_like.remove(db, id=like.id)

    like_in_db = crud.data_product_like.get_by_data_product_id_and_user_id(
        db, data_product_id=sample.obj.id, user_id=sample.user.id
    )
    assert like_in_db is None
