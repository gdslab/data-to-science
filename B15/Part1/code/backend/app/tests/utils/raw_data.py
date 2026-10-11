import os
import shutil

from sqlalchemy.orm import Session

from app import crud, models
from app.core.config import settings
from app.schemas.raw_data import RawDataCreate, RawDataUpdate
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


class SampleRawData:
    """Sample raw data for testing."""

    def __init__(
        self,
        db: Session,
        project: models.Project | None = None,
        flight: models.Flight | None = None,
        user: models.User | None = None,
    ):
        # Set up user, project, and flight
        if not user:
            self.user = create_user(db)
        else:
            self.user = user

        if not project:
            self.project = create_project(db, owner_id=self.user.id)
        else:
            self.project = project

        if not flight:
            self.flight = create_flight(
                db, project_id=self.project.id, pilot_id=self.user.id
            )
        else:
            self.flight = flight

        # Create raw data record in database
        self.obj = self.create_raw_data_in_database(db, "myrawdata.zip", "null")

        # Copy raw data to test directory
        filepath = self.copy_test_raw_data_to_test_directory()

        # Add filepath to database record
        self.update_raw_data_filepath_in_database(db, filepath)

    def copy_test_raw_data_to_test_directory(self) -> tuple[str, str]:
        src_filepath = os.path.join(
            os.sep, "app", "app", "tests", "data", "test_raw_data.zip"
        )
        dest_filepath = os.path.join(
            f"{settings.TEST_STATIC_DIR}/projects/{self.project.id}"
            f"/flights/{self.flight.id}/raw_data/{self.obj.id}/myrawdata.zip"
        )
        if not os.path.exists(os.path.dirname(dest_filepath)):
            os.makedirs(os.path.dirname(dest_filepath))
        shutil.copyfile(src_filepath, dest_filepath)
        return dest_filepath

    def create_raw_data_in_database(self, db: Session, filename: str, filepath: str):
        raw_data_in = RawDataCreate(
            filepath=filepath,
            original_filename=filename,
        )
        raw_data_in_db = crud.raw_data.create_with_flight(
            db, obj_in=raw_data_in, flight_id=self.flight.id
        )
        return raw_data_in_db

    def update_raw_data_filepath_in_database(self, db: Session, filepath: str):
        raw_data_in = RawDataUpdate(
            filepath=filepath, is_initial_processing_completed=True
        )
        return crud.raw_data.update(db, db_obj=self.obj, obj_in=raw_data_in)
