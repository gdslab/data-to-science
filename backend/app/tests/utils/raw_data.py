import os
import shutil

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.flight import Flight
from app.schemas.raw_data import RawDataCreate
from app.tests.utils.flight import create_flight


def create_raw_data(db: Session, flight: Flight | None = None):
    if not flight:
        flight = create_flight(db)
    project_url = f"{settings.TEST_UPLOAD_DIR}/projects/{flight.project_id}"
    src_filepath = os.path.join(os.sep, "app", "app", "tests", "utils", "test.tif")
    dest_filepath = os.path.join(f"{project_url}/flights/{flight.id}/myfile.tif")
    if not os.path.exists(os.path.dirname(dest_filepath)):
        os.makedirs(os.path.dirname(dest_filepath))
    shutil.copyfile(src_filepath, dest_filepath)
    raw_data_in = RawDataCreate(
        filepath=dest_filepath, original_filename=os.path.basename(src_filepath)
    )
    return crud.raw_data.create_with_flight(db, obj_in=raw_data_in, flight_id=flight.id)
