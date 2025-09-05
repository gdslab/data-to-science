import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.schemas.job import State, Status
from app.tests.utils.flight import create_flight
from app.tests.utils.data_product import SampleDataProduct, test_stac_props_dsm
from app.tests.utils.job import create_job
from app.tests.utils.user import create_user


def test_create_data_product(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="ortho")
    assert data_product.obj
    assert data_product.obj.flight_id == data_product.flight.id
    assert data_product.obj.data_type == "ortho"
    assert data_product.obj.original_filename == "myfile.tif"
    assert data_product.obj.stac_properties == test_stac_props_dsm
    assert data_product.obj.is_initial_processing_completed is True
    assert os.path.exists(data_product.obj.filepath)
    assert data_product.obj.created_at is not None
    assert data_product.obj.updated_at is not None
    assert data_product.obj.updated_at >= data_product.obj.created_at


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
    assert (
        stored_data_product.is_initial_processing_completed
        == data_product.obj.is_initial_processing_completed
    )
    assert hasattr(stored_data_product, "url")
    assert hasattr(stored_data_product, "user_style")
    assert stored_data_product.created_at is not None
    assert stored_data_product.updated_at is not None


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
    crud.file_permission.update(
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
    SampleDataProduct(db, flight=flight, user=user, data_type="NDVI")
    SampleDataProduct(db)
    data_products = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_STATIC_DIR, user_id=user.id
    )
    assert type(data_products) is list
    assert len(data_products) == 3
    for data_product in data_products:
        assert data_product.flight_id == flight.id
        assert data_product.public is False


def test_read_data_products_with_multiple_jobs_for_single_data_product(
    db: Session,
) -> None:
    """Test that a data product associated with multiple jobs is not
    included multiple times in the returned results.
    """
    user = create_user(db)
    flight = create_flight(db)
    SampleDataProduct(db, flight=flight, user=user)
    data_product = SampleDataProduct(
        db, flight=flight, user=user, data_type="NDVI", skip_job=True
    ).obj
    # Create two jobs for NDVI data product
    for job_name in ["ndvi-process", "zonal-process"]:
        create_job(
            db,
            name=job_name,
            state=State.COMPLETED,
            status=Status.SUCCESS,
            start_time=datetime.now(tz=timezone.utc),
            data_product_id=data_product.id,
        )
    data_products = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_STATIC_DIR, user_id=user.id
    )
    assert type(data_products) is list
    assert len(data_products) == 2


def test_update_data_product_eo_bands(db: Session) -> None:
    # New band description
    bands_in = [{"name": "b1", "description": "Blue"}]
    # Sample data product object
    data_product = SampleDataProduct(db).obj
    original_created_at = data_product.created_at
    original_updated_at = data_product.updated_at
    # Original data product metadata
    original_metadata = data_product.stac_properties
    # Updated metadata
    updated_metadata = original_metadata.copy()
    updated_metadata["eo"] = bands_in
    # Update data product
    updated_data_product = crud.data_product.update_bands(
        db, data_product_id=data_product.id, updated_metadata=updated_metadata
    )
    assert updated_data_product
    assert updated_data_product.stac_properties["eo"] == bands_in
    assert updated_data_product.created_at == original_created_at
    assert updated_data_product.updated_at > original_updated_at


def test_update_data_product(db: Session) -> None:
    old_data_type = "dsm"
    new_data_type = "dtm"
    data_product = SampleDataProduct(db, data_type=old_data_type)
    original_created_at = data_product.obj.created_at
    original_updated_at = data_product.obj.updated_at
    updated_data_product = crud.data_product.update_data_type(
        db, data_product_id=data_product.obj.id, new_data_type=new_data_type
    )
    assert updated_data_product
    assert updated_data_product.id == data_product.obj.id
    assert updated_data_product.data_type == new_data_type
    assert updated_data_product.created_at == original_created_at
    assert updated_data_product.updated_at > original_updated_at


def test_update_point_cloud_data_product(db: Session) -> None:
    old_data_type = "point_cloud"
    new_data_type = "ortho"
    data_product = SampleDataProduct(db, data_type=old_data_type)
    update_data_product = crud.data_product.update_data_type(
        db, data_product_id=data_product.obj.id, new_data_type=new_data_type
    )
    assert update_data_product
    assert update_data_product.data_type == old_data_type


def test_deactivate_data_product(db: Session) -> None:
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    data_product2 = crud.data_product.deactivate(
        db, data_product_id=data_product.obj.id
    )
    data_product3 = crud.data_product.get(db, id=data_product.obj.id)
    assert data_product2 and data_product3
    assert data_product3.id == data_product.obj.id
    assert data_product3.is_active is False
    assert isinstance(data_product3.deactivated_at, datetime)
    assert data_product3.deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    )
