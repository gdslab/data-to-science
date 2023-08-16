from datetime import date

from sqlalchemy.orm import Session

from app import crud
from app.models.flight import PLATFORMS, SENSORS
from app.schemas.flight import FlightUpdate
from app.tests.utils.flight import create_random_flight
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


def test_create_flight(db: Session) -> None:
    """Verify new flight is created in database."""
    pilot = create_random_user(db)
    project_owner = create_random_user(db)
    project = create_random_project(db, owner_id=project_owner.id)
    acquisition_date = date.today()
    altitude = 100
    side_overlap = 60
    forward_overlap = 75
    flight = create_random_flight(
        db,
        acquisition_date=acquisition_date,
        altitude=altitude,
        side_overlap=side_overlap,
        forward_overlap=forward_overlap,
        sensor=SENSORS[0],
        platform=PLATFORMS[0],
        project_id=project.id,
        pilot_id=pilot.id,
    )
    assert flight
    assert acquisition_date == flight.acquisition_date
    assert altitude == flight.altitude
    assert side_overlap == flight.side_overlap
    assert forward_overlap == flight.forward_overlap
    assert SENSORS[0] == flight.sensor
    assert PLATFORMS[0] == flight.platform
    assert project.id == flight.project_id
    assert pilot.id == flight.pilot_id


def test_get_flight(db: Session) -> None:
    """Verify retrieving flight by id returns correct flight."""
    flight = create_random_flight(db)
    stored_flight = crud.flight.get(db, id=flight.id)
    assert stored_flight
    assert flight.id == stored_flight.id
    assert flight.acquisition_date == stored_flight.acquisition_date
    assert flight.altitude == stored_flight.altitude
    assert flight.side_overlap == stored_flight.side_overlap
    assert flight.forward_overlap == stored_flight.forward_overlap
    assert flight.sensor == stored_flight.sensor
    assert flight.platform == stored_flight.platform
    assert flight.project_id == stored_flight.project_id
    assert flight.pilot_id == stored_flight.pilot_id


def test_update_flight(db: Session) -> None:
    """Verify update changes flight attributes in database."""
    flight = create_random_flight(
        db,
        altitude=60,
        sensor=SENSORS[0],
    )
    flight_in_update = FlightUpdate(
        altitude=100,
        sensor=SENSORS[1],
    )
    flight_update = crud.flight.update(db, db_obj=flight, obj_in=flight_in_update)
    assert flight.id == flight_update.id
    assert flight_in_update.altitude == flight_update.altitude
    assert flight_in_update.sensor == flight_update.sensor
