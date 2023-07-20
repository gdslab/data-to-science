from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.flight import FlightCreate
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


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
    flight_in = FlightCreate(**kwargs)
    return crud.flight.create_flight(
        db, obj_in=flight_in, dataset_id=dataset_id, pilot_id=pilot_id
    )
