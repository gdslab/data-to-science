import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.user_style import UserStyleUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.DefaultUserStyle import DefaultUserStyle
from app.tests.utils.user_style import create_user_style


def test_create_user_style(db: Session) -> None:
    data_product = SampleDataProduct(db)
    user_style = create_user_style(
        db, data_product_id=data_product.obj.id, user_id=data_product.user.id
    )
    assert user_style
    assert user_style.data_product_id == data_product.obj.id
    assert user_style.user_id == data_product.user.id
    assert user_style.settings == DefaultUserStyle().__dict__


def test_read_user_style(db: Session) -> None:
    data_product = SampleDataProduct(db, create_style=True)
    user_style = crud.user_style.get_by_data_product_and_user(
        db, data_product_id=data_product.obj.id, user_id=data_product.user.id
    )
    assert user_style
    assert user_style.data_product_id == data_product.obj.id
    assert user_style.user_id == data_product.user.id


def test_update_user_style(db: Session) -> None:
    data_product = SampleDataProduct(db, create_style=True)
    user_style_in_update = UserStyleUpdate(
        settings=DefaultUserStyle(minimum=50, maximum=75).__dict__
    )
    updated_user_style = crud.user_style.update(
        db, db_obj=data_product.user_style, obj_in=user_style_in_update
    )
    assert updated_user_style
    assert updated_user_style.settings["max"] == 75
    assert updated_user_style.settings["min"] == 50


def test_no_duplicate_user_styles(db: Session) -> None:
    data_product = SampleDataProduct(db)
    create_user_style(
        db, data_product_id=data_product.obj.id, user_id=data_product.user.id
    )
    with pytest.raises(IntegrityError):
        create_user_style(
            db, data_product_id=data_product.obj.id, user_id=data_product.user.id
        )
