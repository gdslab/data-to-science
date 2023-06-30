from datetime import datetime

from sqlalchemy.orm import Session

from app.models.flight import PLATFORMS, SENSORS
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.flight import create_random_flight
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


def test_create_flight(db: Session) -> None:
    """Verify new flight is created in database."""
    pilot = create_random_user(db=db)
    project_owner = create_random_user(db=db)
    project = create_random_project(db=db, owner_id=project_owner.id)
    dataset = create_random_dataset(db=db, category="UAS", project_id=project.id)
    acquisition_date = datetime.now()
    altitude = 100
    side_overlap = 60
    forward_overlap = 75
    flight = create_random_flight(
        db=db,
        acquisition_date=acquisition_date,
        altitude=altitude,
        side_overlap=side_overlap,
        forward_overlap=forward_overlap,
        sensor=SENSORS[0],
        platform=PLATFORMS[0],
        dataset_id=dataset.id,
        pilot_id=pilot.id,
    )
    assert flight
    assert altitude == flight.altitude
    assert side_overlap == flight.side_overlap
    assert forward_overlap == flight.forward_overlap
    assert SENSORS[0] == flight.sensor
    assert PLATFORMS[0] == flight.platform
    assert dataset.id == flight.dataset_id
    assert pilot.id == flight.pilot_id
