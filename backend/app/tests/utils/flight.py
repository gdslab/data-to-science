from datetime import date
from random import randint
from uuid import UUID

from faker import Faker
from sqlalchemy.orm import Session

from app import crud, models
from app.models.flight import PLATFORMS, SENSORS
from app.schemas.flight import FlightCreate
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


faker = Faker()


def create_flight(
    db: Session, project_id: UUID | None = None, pilot_id: UUID | None = None, **kwargs
) -> models.Flight:
    if pilot_id is None:
        pilot = create_user(db)
        pilot_id = pilot.id
    if project_id is None:
        project_owner = create_user(db)
        project = create_project(db, owner_id=project_owner.id)
        project_id = project.id
    if "acquisition_date" not in kwargs:
        acquisition_date = create_acquisition_date()
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
        pilot_id=pilot_id,
    )
    return crud.flight.create_with_project(db, obj_in=flight_in, project_id=project_id)


def create_acquisition_date() -> date:
    """Create random acquisition date from current year."""
    return faker.date_between(
        start_date=date(date.today().year, 1, 1),
        end_date=date(date.today().year, 12, 31),
    )
