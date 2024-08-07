import os
import shutil

from sqlalchemy.orm import Session

from app import crud, models
from app.core.config import settings
from app.schemas.data_product import DataProductCreate, DataProductUpdate
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user
from app.tests.utils.user_style import create_user_style


class SampleDataProduct:
    """Sample data product for testing."""

    def __init__(
        self,
        db: Session,
        data_type: str = "dsm",
        flight: models.Flight | None = None,
        create_style: bool = False,
        project: models.Project | None = None,
        user: models.User | None = None,
        skip_job: bool = False,
        multispectral: bool = False,
    ):
        # Set up user, project, and flight
        self.data_type = data_type
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

        if multispectral:
            self.test_data_product = os.path.join(
                os.sep, "app", "app", "tests", "data", "test_multispectral.tif"
            )
        else:
            self.test_data_product = os.path.join(
                os.sep, "app", "app", "tests", "data", "test.tif"
            )

        # Create data product record database
        self.obj = self.create_data_product_in_database(db, "myfile.tif", "null")

        # Copy data product to test directory
        filepath = self.copy_test_data_product_to_test_directory()

        # Add filepath to database record
        self.update_data_product_filepath_in_database(db, filepath)

        # Create default style setting for the data product
        if create_style:
            self.user_style = create_user_style(
                db, data_product_id=self.obj.id, user_id=self.user.id
            )

        # Create job for the data product
        if not skip_job:
            self.job = create_job(db, data_product_id=self.obj.id)

    def copy_test_data_product_to_test_directory(self) -> tuple[str, str]:
        src_filepath = self.test_data_product
        dest_filepath = os.path.join(
            f"{settings.TEST_STATIC_DIR}/projects/{self.project.id}"
            f"/flights/{self.flight.id}/data_products/{self.obj.id}/myfile.tif"
        )
        if not os.path.exists(os.path.dirname(dest_filepath)):
            os.makedirs(os.path.dirname(dest_filepath))
        shutil.copyfile(src_filepath, dest_filepath)
        return dest_filepath

    def create_data_product_in_database(
        self, db: Session, filename: str, filepath: str
    ):
        data_product_in = DataProductCreate(
            data_type=self.data_type,
            filepath=filepath,
            original_filename=filename,
            stac_properties=test_stac_props_dsm,
        )
        data_product_in_db = crud.data_product.create_with_flight(
            db, obj_in=data_product_in, flight_id=self.flight.id
        )
        return data_product_in_db

    def update_data_product_filepath_in_database(self, db: Session, filepath: str):
        data_product_in = DataProductUpdate(
            filepath=filepath, is_initial_processing_completed=True
        )
        return crud.data_product.update(db, db_obj=self.obj, obj_in=data_product_in)


test_stac_props_dsm = {
    "raster": [
        {
            "data_type": "float32",
            "stats": {
                "minimum": 187.264,
                "maximum": 188.761,
                "mean": 187.502,
                "stddev": 0.257,
            },
            "nodata": None,
            "unit": "metre",
        }
    ],
    "eo": [{"name": "b1", "description": "Gray"}],
}

test_stac_props_ortho = {
    "raster": [
        {
            "data_type": "float32",
            "stats": {
                "minimum": 181.047,
                "maximum": 189.516,
                "mean": 187.329,
                "stddev": 0.675,
            },
            "nodata": None,
            "unit": "metre",
        }
    ],
    "eo": [
        {"name": "b1", "description": "Red"},
        {"name": "b2", "description": "Green"},
        {"name": "b3", "description": "Blue"},
        {"name": "b4", "description": "Alpha"},
    ],
}
