import os

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.flight import create_flight
from app.tests.utils.data_product import create_data_product


def test_create_data_product(db: Session) -> None:
    """Verify new data record created in database."""
    flight = create_flight(db)
    data_product = create_data_product(db, data_type="ortho", flight=flight)
    assert data_product
    assert data_product.flight_id == flight.id
    assert data_product.data_type == "ortho"
    assert data_product.original_filename == "test.tif"
    assert os.path.exists(data_product.filepath)


def test_get_data_product(db: Session) -> None:
    """Verify retrieving data product by id returns correct record."""
    flight = create_flight(db)
    data_product = create_data_product(db, data_type="dsm", flight=flight)
    stored_data_product = crud.data_product.get_single_by_id(
        db, data_product_id=data_product.id, upload_dir=settings.TEST_UPLOAD_DIR
    )
    assert stored_data_product
    assert stored_data_product.id == data_product.id
    assert stored_data_product.flight_id == flight.id
    assert stored_data_product.data_type == data_product.data_type
    assert stored_data_product.filepath == data_product.filepath
    assert stored_data_product.original_filename == data_product.original_filename
    assert stored_data_product.url


def test_get_all_data_product(db: Session) -> None:
    """Verify retrieval of all data products associated with flight."""
    flight = create_flight(db)
    other_flight = create_flight(db)
    create_data_product(db, flight=flight)
    create_data_product(db, flight=flight)
    create_data_product(db, flight=flight)
    create_data_product(db, flight=other_flight)
    all_data_product = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_UPLOAD_DIR
    )
    assert type(all_data_product) is list
    assert len(all_data_product) == 3
    for data_product in all_data_product:
        assert data_product.flight_id == flight.id
