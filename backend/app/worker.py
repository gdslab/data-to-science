import os
from uuid import UUID

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app

from app.utils.ImageProcessor import ImageProcessor


@celery_app.task(name="test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(name="geotiff_upload_task")
def process_geotiff(
    filename: str,
    out_path: str,
    project_id: UUID,
    flight_id: UUID,
    test: bool = False,
) -> None:
    db = next(get_db())
    crud.raw_data.create_with_flight(
        db,
        schemas.RawDataCreate(
            filepath=out_path.replace("__temp", ""),
            original_filename=os.path.basename(filename),
        ),
        flight_id=flight_id,
    )
    # create COG for uploaded GeoTIFF if necessary
    ip = ImageProcessor(out_path)
    ip.run()

    return None
