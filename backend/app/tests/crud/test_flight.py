from datetime import date

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.flight import PLATFORMS, SENSORS
from app.schemas.flight import FlightUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def test_create_flight(db: Session) -> None:
    pilot = create_user(db)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    acquisition_date = date.today()
    altitude = 100
    side_overlap = 60
    forward_overlap = 75
    flight = create_flight(
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
    flight = create_flight(db)
    stored_flight = crud.flight.get_flight_by_id(
        db, project_id=flight.project_id, flight_id=flight.id
    )
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


def test_get_flights(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    other_project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=other_project.id)
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert type(flights) is list
    assert len(flights) == 3
    for flight in flights:
        assert flight.project_id == project.id


def test_get_flights_excluding_processing_or_failed_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(
        db, data_type="ortho", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        "test-job-1",
        state="COMPLETED",
        status="FAILED",
        data_product_id=data_product1.obj.id,
    )
    data_product2 = SampleDataProduct(
        db, data_type="dsm", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        "test-job-2",
        state="COMPLETED",
        status="SUCCESS",
        data_product_id=data_product2.obj.id,
    )
    data_product3 = SampleDataProduct(
        db, data_type="ortho", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        "test-job-3",
        state="PENDING",
        status="SUCCESS",
        data_product_id=data_product3.obj.id,
    )
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=user.id,
        include_all=False,
    )
    assert type(flights) is list
    assert len(flights) == 1
    assert len(flights[0].data_products) == 1
    print(flights[0].data_products[0].data_type)
    assert flights[0].data_products[0].data_type == "dsm"


def test_update_flight(db: Session) -> None:
    flight = create_flight(db, altitude=60, sensor=SENSORS[0])
    flight_in_update = FlightUpdate(altitude=100, sensor=SENSORS[1])
    flight_update = crud.flight.update(db, db_obj=flight, obj_in=flight_in_update)
    assert flight.id == flight_update.id
    assert flight_in_update.altitude == flight_update.altitude
    assert flight_in_update.sensor == flight_update.sensor


def test_get_flight_for_deactivated_project_returns_none(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id)
    flight2 = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight.id
    )
    assert flight2 is None


def test_get_flights_ignores_deactivated_project(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id)
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert type(flights) is list
    assert len(flights) == 0
