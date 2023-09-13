import os
import shutil

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.flight import Flight
from app.schemas.data_product import DataProductCreate
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job


test_band_info = {
    "band_info": [
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
}


def create_data_product(
    db: Session, data_type: str = "dsm", flight: Flight | None = None
):
    if not flight:
        flight = create_flight(db)
    project_url = f"{settings.TEST_UPLOAD_DIR}/projects/{flight.project_id}"
    src_filepath = os.path.join(os.sep, "app", "app", "tests", "data", "test.tif")
    dest_filepath = os.path.join(f"{project_url}/flights/{flight.id}/myfile.tif")
    if not os.path.exists(os.path.dirname(dest_filepath)):
        os.makedirs(os.path.dirname(dest_filepath))
    shutil.copyfile(src_filepath, dest_filepath)
    data_product_in = DataProductCreate(
        band_info=test_band_info,
        data_type=data_type,
        filepath=dest_filepath,
        original_filename=os.path.basename(src_filepath),
    )
    data_product = crud.data_product.create_with_flight(
        db, obj_in=data_product_in, flight_id=flight.id
    )
    create_job(db, data_product_id=data_product.id)
    return data_product
