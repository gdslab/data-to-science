import os

from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.flight import create_flight
from app.tests.utils.raw_data import create_raw_data


def test_create_raw_data(db: Session) -> None:
    """Verify new data record created in database."""
    flight = create_flight(db)
    path_to_data = os.path.join(os.sep, "/tmp", "myfile.tif")
    raw_data = create_raw_data(db, flight_id=flight.id, filepath=path_to_data)
    assert raw_data
    assert path_to_data == raw_data.filepath
    assert flight.id == raw_data.flight_id


def test_get_raw_data(db: Session) -> None:
    """Verify retrieving raw data by id returns correct record."""
    flight = create_flight(db)
    raw_data = create_raw_data(db, flight_id=flight.id)
    stored_raw_data = crud.raw_data.get(db, id=raw_data.id)
    assert stored_raw_data
    assert raw_data.id == stored_raw_data.id
    assert flight.id == stored_raw_data.flight_id
    assert raw_data.filepath == stored_raw_data.filepath


def test_get_all_raw_data(db: Session) -> None:
    """Verify retrieval of all raw data associated with flight."""
    flight = create_flight(db)
    other_flight = create_flight(db)
    create_raw_data(db, flight_id=flight.id)
    create_raw_data(db, flight_id=flight.id)
    create_raw_data(db, flight_id=flight.id)
    create_raw_data(db, flight_id=other_flight.id)
    all_raw_data = crud.raw_data.get_multi_by_flight(db, flight_id=flight.id)
    assert type(all_raw_data) is list
    assert len(all_raw_data) == 3
    for raw_data in all_raw_data:
        assert raw_data.flight_id == flight.id
