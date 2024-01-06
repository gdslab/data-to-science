import os

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.flight import create_flight
from app.tests.utils.data_product import SampleDataProduct, test_stac_props_dsm
from app.tests.utils.user import create_user


def test_create_data_product(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="ortho")
    assert data_product.obj
    assert data_product.obj.flight_id == data_product.flight.id
    assert data_product.obj.data_type == "ortho"
    assert data_product.obj.original_filename == "test.tif"
    assert data_product.obj.stac_properties == test_stac_props_dsm
    assert os.path.exists(data_product.obj.filepath)


def test_read_data_product(db: Session) -> None:
    data_product = SampleDataProduct(db, create_style=True)
    stored_data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product.obj.id,
        upload_dir=settings.TEST_STATIC_DIR,
        user_id=data_product.user.id,
    )
    assert stored_data_product
    assert stored_data_product.id == data_product.obj.id
    assert stored_data_product.flight_id == data_product.flight.id
    assert stored_data_product.stac_properties == test_stac_props_dsm
    assert stored_data_product.data_type == data_product.obj.data_type
    assert stored_data_product.filepath == data_product.obj.filepath
    assert stored_data_product.original_filename == data_product.obj.original_filename
    assert stored_data_product.url
    assert stored_data_product.user_style


def test_read_public_data_product_by_id(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    assert file_permission
    file_permission_in_update = FilePermissionUpdate(is_public=True)
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )
    stored_data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product.id, upload_dir=settings.TEST_STATIC_DIR
    )
    assert stored_data_product
    assert stored_data_product.id == data_product.id
    assert stored_data_product.file_permission.is_public is True


def test_read_restricted_data_product_with_public_get_by_id(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    assert file_permission
    file_permission_in_update = FilePermissionUpdate(is_public=False)
    file_permission_update = crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )
    stored_data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product.id, upload_dir=settings.TEST_STATIC_DIR
    )
    assert stored_data_product is None


def test_read_data_products(db: Session) -> None:
    user = create_user(db)
    flight = create_flight(db)
    SampleDataProduct(db, flight=flight, user=user)
    SampleDataProduct(db, flight=flight, user=user)
    SampleDataProduct(db, flight=flight, user=user)
    SampleDataProduct(db)
    data_products = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_STATIC_DIR, user_id=user.id
    )
    assert type(data_products) is list
    assert len(data_products) == 3
    for data_product in data_products:
        assert data_product.flight_id == flight.id
        assert data_product.public is False
