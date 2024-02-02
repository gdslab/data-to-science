import os
import shutil

from sqlalchemy.orm import Session

from app import crud, models
from app.core.config import settings
from app.schemas.raw_data import RawDataCreate
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

        # Copy raw data to test directory
        filename, filepath = self.copy_test_raw_data_to_test_directory()

        # Create raw data record in database
        self.obj = self.create_raw_data_in_database(db, filename, filepath)

    def copy_test_raw_data_to_test_directory(self) -> tuple[str, str]:
        src_filepath = os.path.join(
            os.sep, "app", "app", "tests", "data", "test_raw_data.zip"
        )
        dest_filepath = os.path.join(
            f"{settings.TEST_STATIC_DIR}/projects/{self.project.id}"
            f"/flights/{self.flight.id}/myrawdata.zip"
        )
        if not os.path.exists(os.path.dirname(dest_filepath)):
            os.makedirs(os.path.dirname(dest_filepath))
        shutil.copyfile(src_filepath, dest_filepath)
        return os.path.basename(src_filepath), dest_filepath

    def create_raw_data_in_database(self, db: Session, filename: str, filepath: str):
        raw_data_in = RawDataCreate(
            filepath=filepath,
            original_filename=filename,
        )
        raw_data_in_db = crud.raw_data.create_with_flight(
            db, obj_in=raw_data_in, flight_id=self.flight.id
        )
        return raw_data_in_db
