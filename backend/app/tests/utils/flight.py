from datetime import datetime
from random import randint
from uuid import UUID

from faker import Faker
from sqlalchemy.orm import Session

from app import crud, models
from app.models.flight import PLATFORMS, SENSORS
from app.schemas.flight import FlightCreate
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


faker = Faker()


def create_random_flight(
    db: Session, dataset_id: UUID | None = None, pilot_id: UUID | None = None, **kwargs
) -> models.Flight:
    if pilot_id is None:
        pilot = create_random_user(db)
        pilot_id = pilot.id
    if dataset_id is None:
        project_owner = create_random_user(db)
        project = create_random_project(db, owner_id=project_owner.id)
        dataset = create_random_dataset(db, category="UAS", project_id=project.id)
        dataset_id = dataset.id
    if "acquisition_date" not in kwargs:
        acquisition_date = create_random_acquisition_date()
    else:
        acquisition_date = kwargs["acquisition_date"]
    if "altitude" not in kwargs:
        altitude = randint(0, 500)
    else:
        altitude = kwargs["altitude"]
    if "side_overlap" not in kwargs:
        side_overlap = randint(40, 80)
    else:
        side_overlap = kwargs["side_overlap"]
    if "forward_overlap" not in kwargs:
        forward_overlap = randint(40, 80)
    else:
        forward_overlap = kwargs["forward_overlap"]
    if "sensor" not in kwargs:
        sensor = SENSORS[randint(0, len(SENSORS) - 1)]
    else:
        sensor = kwargs["sensor"]
    if "platform" not in kwargs:
        platform = PLATFORMS[randint(0, len(PLATFORMS) - 1)]
    else:
        platform = kwargs["platform"]
    flight_in = FlightCreate(
        acquisition_date=acquisition_date,
        altitude=altitude,
        side_overlap=side_overlap,
        forward_overlap=forward_overlap,
        sensor=sensor,
        platform=platform,
        dataset_id=dataset_id,
        pilot_id=pilot_id,
    )
    return crud.flight.create_with_dataset(db, obj_in=flight_in, dataset_id=dataset_id)


def create_random_acquisition_date() -> datetime:
    """Create random acquisition date from current year."""
    return faker.date_time_between(
        start_date=datetime(datetime.today().year, 1, 1),
        end_date=datetime(datetime.today().year, 12, 31),
    )