"""Celery tasks for processing uploaded files."""

import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

import geopandas as gpd
import pandas as pd
from celery.utils.log import get_task_logger
from fastapi.encoders import jsonable_encoder

from app import crud, schemas
from app.api.deps import get_db
from app.utils.date_utils import parse_date
from app.api.utils import (
    is_geometry_match,
    save_vector_layer_parquet,
    save_vector_layer_flatgeobuf,
    get_static_dir,
)
from app.core.celery_app import celery_app
from app.utils.ImageProcessor import ImageProcessor, get_utm_epsg_from_latlon
from app.utils.job_manager import JobManager
from app.utils.TarProcessor import TarProcessor
from app.schemas.data_product import DataProductUpdate
from app.schemas.job import Status
from app.tasks.utils import validate_3dgs_image, validate_panoramic_image
from app.utils.lcc_validator import unpack_lcc_zip


logger = get_task_logger(__name__)

# 32 MB buffer size for copying files
BUFFER_SIZE = 32 * 1024 * 1024


@celery_app.task(name="upload_3dgs_task")
def upload_3dgs(
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
    data_product_id: UUID,
) -> None:
    """Celery task for processing an uploaded 3D Gaussian Splatting image.

    Args:
        storage_path (str): Filepath for 3D Gaussian Splatting image in tusd storage.
        destination_filepath (str): Filepath for 3D Gaussian Splatting image in static files.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded 3D Gaussian Splatting image.
    """
    in_image = Path(storage_path)
    out_image = Path(destination_filepath)

    # copy uploaded panoramic image to static files
    with open(storage_path, "rb") as src, open(out_image, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_image):
            shutil.rmtree(in_image.parents[1])
        logger.error("Could not find job in DB for upload process")
        return None

    # validate uploaded 3D Gaussian Splatting image
    is_valid, error_message = validate_3dgs_image(str(out_image))
    if not is_valid:
        # remove uploaded file and raise exception
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
        # remove output image
        if os.path.exists(out_image):
            os.remove(out_image)

        job.update(status=Status.FAILED)
        logger.error(f"Invalid 3D Gaussian Splatting image: {error_message}")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
        # remove output image
        if os.path.exists(out_image):
            os.remove(out_image)

        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # update data product filepath to 3D Gaussian Splatting image
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=str(out_image), is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded 3D Gaussian Splatting image from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


@celery_app.task(name="upload_3dgs_lcc_task")
def upload_3dgs_lcc(
    storage_path: str,
    data_product_dir: str,
    job_id: UUID,
    data_product_id: UUID,
) -> None:
    """Celery task for processing an uploaded 3D Gaussian Splatting LCC zip file.

    The zip file is expected to contain XGrids LCC format files (*.lcc, index.bin, data.bin).
    The zip is validated and extracted to the data product directory.

    Args:
        storage_path (str): Filepath for LCC zip file in tusd storage.
        data_product_dir (str): Directory for extracted LCC files.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded 3DGS LCC.
    """
    output_dir = Path(data_product_dir)

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # copy zip to data product directory for extraction
    temp_zip_path = output_dir / "temp_lcc.zip"
    try:
        with open(storage_path, "rb") as src, open(temp_zip_path, "wb") as dst:
            shutil.copyfileobj(src, dst, length=BUFFER_SIZE)
    except Exception:
        job.update(status=Status.FAILED)
        logger.exception("Failed to copy LCC zip to data product directory")
        return None

    # validate and extract LCC zip
    try:
        lcc_filepath = unpack_lcc_zip(temp_zip_path, output_dir)
    except FileNotFoundError as e:
        job.update(status=Status.FAILED)
        logger.error(f"LCC zip file not found: {e}")
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        return None
    except ValueError as e:
        job.update(status=Status.FAILED)
        logger.error(f"Invalid LCC zip file: {e}")
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        return None
    except Exception:
        job.update(status=Status.FAILED)
        logger.exception("Failed to extract LCC zip file")
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        return None

    # remove temp zip file after successful extraction
    try:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
    except Exception:
        logger.exception("Failed to remove temp zip file")

    # update data product filepath to the extracted .lcc file
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=lcc_filepath, is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded LCC zip from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


@celery_app.task(name="upload_geotiff_task")
def upload_geotiff(
    storage_path: str,
    geotiff_filepath: str,
    user_id: UUID,
    job_id: UUID,
    data_product_id: UUID,
    project_to_utm: bool = False,
) -> None:
    """Celery task for processing an uploaded GeoTIFF.

    Args:
        storage_path (Path): Filepath for GeoTIFF in tusd storage.
        geotiff_filepath (str): Filepath for GeoTIFF.
        user_id (UUID): User ID for user that uploaded GeoTIFF.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded GeoTIFF.
        project_to_utm (bool): Whether to project the GeoTIFF to UTM.
    """
    in_raster = Path(geotiff_filepath)

    # copy uploaded GeoTIFF to static files
    with open(storage_path, "rb") as src, open(in_raster, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)

        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # create get STAC properties and convert to COG (if needed)
    try:
        ip = ImageProcessor(str(in_raster), project_to_utm=project_to_utm)
        out_raster = ip.run()
        default_symbology = ip.get_default_symbology()
    except Exception:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        job.update(status=Status.FAILED)
        logger.exception("Failed to process uploaded GeoTIFF")
        return None

    # update data product with STAC properties
    try:
        crud.data_product.update(
            db,
            db_obj=data_product,
            obj_in=DataProductUpdate(
                filepath=str(out_raster),
                stac_properties=jsonable_encoder(ip.stac_properties),
            ),
        )
    except Exception:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        job.update(status=Status.FAILED)
        logger.exception("Failed to update data product in db")
        return None

    # indicate initial processing finished without errors
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(is_initial_processing_completed=True),
    )

    # create user style record for data product and user
    crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=default_symbology,
        data_product_id=data_product.id,
        user_id=user_id,
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded geotiff from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


def extract_dates_from_indoor_spreadsheet(
    file_path: str, indoor_project_data_id: UUID
) -> tuple[datetime | None, datetime | None]:
    """Extract planting date and scan date range from indoor project spreadsheet.

    Args:
        file_path (str): Path to the Excel spreadsheet
        indoor_project_data_id (UUID): ID for logging purposes

    Returns:
        tuple[datetime | None, datetime | None]: (start_date, end_date) where:
            - start_date is PLANTING_DATE from PPEW, or min SCAN_DATE from Top
            - end_date is max SCAN_DATE from Top
            Either can be None if extraction fails
    """
    try:
        # Read PPEW worksheet
        ppew_df = None
        try:
            ppew_df = pd.read_excel(
                file_path, sheet_name="PPEW", dtype={"VARIETY": str, "PI": str}
            )
        except ValueError:
            logger.warning(f"PPEW worksheet not found in {indoor_project_data_id}")

        # Read Top worksheet
        top_df = None
        try:
            top_df = pd.read_excel(file_path, sheet_name="Top", dtype={"VARIETY": str})
        except ValueError:
            logger.warning(f"Top worksheet not found in {indoor_project_data_id}")

        # Initialize return values
        start_date = None
        end_date = None

        # Extract planting_date from PPEW worksheet
        if ppew_df is not None and not ppew_df.empty:
            # Normalize column names (lowercase, replace spaces with underscores)
            ppew_df.columns = ppew_df.columns.str.lower()
            ppew_df.columns = ppew_df.columns.str.replace(" ", "_")

            if "planting_date" in ppew_df.columns:
                try:
                    planting_date_series = ppew_df["planting_date"].dropna()
                    if not planting_date_series.empty:
                        planting_date_value = planting_date_series.iloc[0]
                        start_date = parse_date(planting_date_value)
                        logger.info(f"Extracted planting_date: {start_date}")
                except Exception as e:
                    logger.warning(f"Failed to parse planting_date: {e}")

        # Extract min/max scan_date from Top worksheet
        if top_df is not None and not top_df.empty:
            # Normalize column names
            top_df.columns = top_df.columns.str.lower()
            top_df.columns = top_df.columns.str.replace(" ", "_")

            if "scan_date" in top_df.columns:
                try:
                    # Drop NaN values before parsing to avoid errors
                    scan_dates = top_df["scan_date"].dropna()

                    # Ensure scan_date is datetime type
                    if (
                        not scan_dates.empty
                        and not pd.api.types.is_datetime64_any_dtype(scan_dates)
                    ):
                        scan_dates = scan_dates.apply(parse_date)
                    if not scan_dates.empty:
                        min_scan_date = scan_dates.min()
                        max_scan_date = scan_dates.max()

                        # Use min_scan_date as fallback for start_date if planting_date not found
                        if start_date is None:
                            start_date = (
                                min_scan_date.to_pydatetime()
                                if hasattr(min_scan_date, "to_pydatetime")
                                else min_scan_date
                            )
                            logger.info(
                                f"Using min scan_date as start_date: {start_date}"
                            )

                        # Use max_scan_date as end_date
                        end_date = (
                            max_scan_date.to_pydatetime()
                            if hasattr(max_scan_date, "to_pydatetime")
                            else max_scan_date
                        )
                        logger.info(f"Extracted max scan_date as end_date: {end_date}")
                except Exception as e:
                    logger.warning(f"Failed to parse scan_date: {e}")

        return start_date, end_date

    except Exception as e:
        logger.exception(
            f"Unexpected error extracting dates from {indoor_project_data_id}: {e}"
        )
        return None, None


@celery_app.task(name="upload_indoor_project_data_task")
def upload_indoor_project_data(
    indoor_project_data_id: UUID,
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
) -> None:
    """Celery task for copying uploaded indoor project data (.xls, .xlsx, or .tar)
    to static files location.

    Args:
        indoor_project_data_id (UUID): ID for indoor project data record.
        storage_path (Path): Location of indoor project data on tusd server.
        destination_filepath (Path): Destination in static files directory for data.
        job_id (UUID): ID for job tracking task progress.
    """
    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve indoor project data associated with this task
    indoor_project_data = crud.indoor_project_data.get(db, id=indoor_project_data_id)
    if not indoor_project_data:
        logger.error(f"Unable to find indoor project data: {indoor_project_data_id}")
        job.update(status=Status.FAILED)
        return None

    job.start()

    try:
        logger.info("Copying uploaded indoor project data from tusd to user volume...")

        # copy uploaded indoor project data to static files and update filepath
        with open(storage_path, "rb") as src, open(destination_filepath, "wb") as dst:
            shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

        # add filepath to indoor project data
        indoor_project_data_update_in = (
            schemas.indoor_project_data.IndoorProjectDataUpdate(
                file_path=str(destination_filepath)
            )
        )
        indoor_project_data_updated = crud.indoor_project_data.update(
            db, db_obj=indoor_project_data, obj_in=indoor_project_data_update_in
        )
        logger.info(indoor_project_data_updated)

        logger.info(
            "Copying uploaded indoor project data from tusd to user volume...Done!"
        )
    except Exception:
        logger.exception(
            f"Failed to process uploaded indoor data: {indoor_project_data_id}"
        )
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        job.update(status=Status.FAILED)
        return None

    # extract contents if this is a tar archive
    if tarfile.is_tarfile(destination_filepath):
        logger.info("Extracting indoor project data tar archive contents...")
        try:
            tar_processor = TarProcessor(tar_file_path=destination_filepath)
            tar_processor.extract()
        except Exception:
            logger.exception(f"Failed to extract tar archive at {destination_filepath}")
            # clean up any files
            if os.path.exists(destination_filepath):
                os.remove(destination_filepath)
            job.update(status=Status.FAILED)
            return None

        # remove tar after extraction finishes
        tar_processor.remove()

        logger.info("Extracting indoor project data tar archive contents...Done!")
    else:
        # For non-tar files, try to extract dates if it's an xlsx file
        if destination_filepath.lower().endswith(".xlsx"):
            logger.info(
                f"Attempting to extract dates from spreadsheet: {indoor_project_data_id}"
            )

            try:
                # Extract dates from spreadsheet
                extracted_start, extracted_end = extract_dates_from_indoor_spreadsheet(
                    destination_filepath, indoor_project_data_id
                )

                # Fetch the parent indoor_project (must explicitly get it)
                indoor_project = crud.indoor_project.get(
                    db, id=indoor_project_data.indoor_project_id
                )

                if not indoor_project:
                    logger.warning(
                        f"Could not find indoor project {indoor_project_data.indoor_project_id} "
                        f"to update dates"
                    )
                else:
                    # Build update dict with only dates that aren't already set
                    update_data: dict[str, datetime] = {}

                    # Only update start_date if not already set
                    if (
                        indoor_project.start_date is None
                        and extracted_start is not None
                    ):
                        # Validate that extracted start_date doesn't come after existing end_date
                        if (
                            indoor_project.end_date is not None
                            and extracted_start > indoor_project.end_date
                        ):
                            logger.warning(
                                f"Extracted start_date {extracted_start} comes after existing end_date "
                                f"{indoor_project.end_date}, not setting start_date"
                            )
                        else:
                            update_data["start_date"] = extracted_start
                            logger.info(f"Setting start_date to {extracted_start}")

                    # Only update end_date if not already set
                    if indoor_project.end_date is None and extracted_end is not None:
                        # Validate that extracted end_date doesn't come before existing start_date
                        if (
                            indoor_project.start_date is not None
                            and extracted_end < indoor_project.start_date
                        ):
                            logger.warning(
                                f"Extracted end_date {extracted_end} comes before existing start_date "
                                f"{indoor_project.start_date}, not setting end_date"
                            )
                        else:
                            update_data["end_date"] = extracted_end
                            logger.info(f"Setting end_date to {extracted_end}")

                    # Update if we have any dates to set
                    if update_data:
                        crud.indoor_project.update(
                            db,
                            db_obj=indoor_project,
                            obj_in=schemas.indoor_project.IndoorProjectUpdate(
                                **update_data
                            ),
                        )
                        logger.info(
                            f"Successfully updated indoor project dates: {update_data}"
                        )
                    else:
                        logger.info(
                            "No date updates needed - dates already set or not extracted"
                        )

            except Exception as e:
                logger.exception(
                    f"Failed to extract/update dates for {indoor_project_data_id}, "
                    f"continuing with upload: {e}"
                )

    # update indoor project data to indicate initial processing is complete
    crud.indoor_project_data.update(
        db,
        db_obj=indoor_project_data_updated,
        obj_in=schemas.indoor_project_data.IndoorProjectDataUpdate(
            is_initial_processing_completed=True
        ),
    )

    job.update(status=Status.SUCCESS)

    # remove indoor project data from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception(
            f"Unable to cleanup indoor project data upload on tusd server: {indoor_project_data_id}"
        )
    finally:
        return None


@celery_app.task(name="upload_panoramic_task")
def upload_panoramic(
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
    data_product_id: UUID,
) -> None:
    """Celery task for processing an uploaded panoramic image.

    Args:
        storage_path (str): Filepath for panoramic image in tusd storage.
        destination_filepath (str): Filepath for panoramic image in static files.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded panoramic image.
    """
    in_image = Path(storage_path)
    out_image = Path(destination_filepath)

    # copy uploaded panoramic image to static files
    with open(storage_path, "rb") as src, open(out_image, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_image):
            shutil.rmtree(in_image.parents[1])
        logger.error("Could not find job in DB for upload process")
        return None

    # validate uploaded panoramic image
    is_valid, error_message = validate_panoramic_image(str(out_image))
    if not is_valid:
        # remove uploaded file and raise exception
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
        # remove output image
        if os.path.exists(out_image):
            os.remove(out_image)

        job.update(status=Status.FAILED)
        logger.error(f"Invalid panoramic image: {error_message}")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
        # remove output image
        if os.path.exists(out_image):
            os.remove(out_image)

        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # update data product filepath to panoramic image
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=str(out_image), is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded panoramic image from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


@celery_app.task(name="upload_point_cloud_task")
def upload_point_cloud(
    storage_path: str,
    las_filepath: str,
    job_id: UUID,
    data_product_id: UUID,
    project_to_utm: bool = False,
) -> str | None:
    """Celery task for converting uploaded las/laz point cloud to cloud optimized
    point cloud format. Untwine performs the conversion

    Args:
        storage_path (str): Filepath for point cloud in tusd storage.
        las_filepath (str): Filepath for point cloud.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded point cloud.

    Raises:
        Exception: Raise if EPT or COPG subprocesses fail.
    """
    in_las = Path(las_filepath)

    logger.info(f"Input point cloud filepath: {in_las}")

    # copy uploaded point cloud to static files
    with open(storage_path, "rb") as src, open(in_las, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        # remove job if exists
        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # create cloud optimized point cloud
    try:
        # construct path for compressed COPC
        if in_las.name.endswith(".copc.laz"):
            # copy the file to parent directory using buffered copy
            with open(in_las, "rb") as src, open(
                in_las.parents[1] / in_las.name, "wb"
            ) as dst:
                shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

            copc_laz_filepath = in_las.parents[1] / in_las.name
        else:
            copc_laz_filepath = in_las.parents[1] / in_las.with_suffix(".copc.laz").name
            # get UTM EPSG code if needed
            if project_to_utm:
                # read the point cloud metadata
                pdal_info_cmd: list[str] = [
                    "pdal",
                    "info",
                    "--summary",
                    str(in_las),
                ]
                pdal_info_result = subprocess.run(
                    pdal_info_cmd, stdout=subprocess.PIPE, check=True
                )
                pdal_info_json = json.loads(pdal_info_result.stdout)

                # get the bounding box of the point cloud
                minx = pdal_info_json["summary"]["bounds"]["minx"]
                maxx = pdal_info_json["summary"]["bounds"]["maxx"]
                miny = pdal_info_json["summary"]["bounds"]["miny"]
                maxy = pdal_info_json["summary"]["bounds"]["maxy"]

                # calculate the center point of the bounding box
                mean_x = (minx + maxx) / 2
                mean_y = (miny + maxy) / 2

                # check if the point cloud is in WGS84
                if not (-180 <= mean_x <= 180 and -90 <= mean_y <= 90):
                    logger.error(
                        f"Point cloud coordinates outside WGS84 bounds: lon={mean_x}, lat={mean_y}"
                    )
                    # leave the point cloud in its original CRS
                    epsg_code = None
                else:
                    epsg_code = get_utm_epsg_from_latlon(mean_y, mean_x)

            # use pdal info to find the EPSG code of the point cloud
            untwine_cmd: list[str] = [
                "untwine",
                "-i",
                str(in_las),
                "-o",
                str(copc_laz_filepath),
            ]

            # project to UTM if flag set and UTM EPSG code found
            if project_to_utm and epsg_code:
                untwine_cmd.extend(["--a_srs", epsg_code])

            # run untwine command
            subprocess.run(untwine_cmd)

            # clean up temp directory created by untwine
            if os.path.exists(f"{copc_laz_filepath}_tmp"):
                shutil.rmtree(f"{copc_laz_filepath}_tmp")
    except Exception:
        logger.exception("Failed to build COPC from uploaded point cloud")
        shutil.rmtree(in_las.parents[1])
        job.update(status=Status.FAILED)
        return None

    # update data product filepath to copc.laz
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=str(copc_laz_filepath), is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded point cloud from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return str(in_las)


@celery_app.task(name="upload_raw_data_task")
def upload_raw_data(
    raw_data_id: UUID,
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
    project_id: UUID,
    user_id: UUID,
) -> None:
    """Celery task for copying uploaded raw data (.zip) to static files location.

    Args:
        raw_data_id (UUID): ID for raw data record.
        storage_path (Path): Location of raw data on tusd server.
        destination_filepath (Path): Destination in static files directory for raw data.
        job_id (UUID): ID for job tracking task progress.
        project_ID (UUID): ID for project associated with raw data.
        user_id (UUID): ID for user associated with raw data upload.
    """
    # 128 MB buffer size for copying files
    BUFFER_SIZE = 128 * 1024 * 1024

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve raw data associated with this task
    raw_data = crud.raw_data.get(db, id=raw_data_id)
    if not raw_data:
        logger.error("Unable to find raw data record")
        return None

    # update job status to indicate process has started
    job.start()
    try:
        # copy uploaded raw data to static files and update record
        with open(storage_path, "rb") as src, open(destination_filepath, "wb") as dst:
            shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

        # add filepath to raw data object
        crud.raw_data.update(
            db,
            db_obj=raw_data,
            obj_in=schemas.RawDataUpdate(
                filepath=str(destination_filepath), is_initial_processing_completed=True
            ),
        )
    except Exception:
        logger.exception("Failed to process uploaded raw data")
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        # remove job
        job.update(status=Status.FAILED)
        return None

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove raw data from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")


@celery_app.task(name="upload_vector_layer_task")
def upload_vector_layer(
    file_path: str,
    original_file_name: str,
    project_id: UUID,
    job_id: UUID,
) -> None:
    # Max number of allowed features
    # VECTOR_FEATURE_LIMIT = 250000

    # Clean up temp file
    def cleanup(job: JobManager) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.exception("Unable to cleanup uploaded file")
            job.update(status=Status.FAILED)

    # get database session
    db = next(get_db())
    # retrieve job associated with task
    job = JobManager(job_id=job_id)
    # update job status to indicate process has started
    job.start()

    # confirm uploaded file exists on disk
    try:
        assert os.path.exists(file_path)
    except AssertionError:
        logger.exception("Cannot find uploaded file on disk")
        job.update(status=Status.FAILED)
        return None

    # read uploaded file into geopandas dataframe
    try:
        gdf = gpd.read_file(file_path)
    except Exception:
        logger.exception("Failed to read uploaded vector layer file")
        job.update(status=Status.FAILED)
        cleanup(job)
        return None

    # check number of features
    if len(gdf) == 0:
        logger.error("Uploaded vector layer does not have any features")
        job.update(
            status=Status.FAILED,
            extra={
                "status": 0,
                "detail": "No features. Vector layer must have at least one feature.",
            },
        )

    # check for consistent geometry type
    first_feature_geometry_type = gdf.iloc[0].geometry.geom_type
    for _, row in gdf.iterrows():
        if not is_geometry_match(
            expected_geometry=first_feature_geometry_type,
            actual_geometry=row.geometry.geom_type,
        ):
            logger.error("Inconsistent geometry types in uploaded vector layer")

    # add vector layer to database
    try:
        features = crud.vector_layer.create_with_project(
            db, file_name=original_file_name, gdf=gdf, project_id=project_id
        )
    except Exception:
        logger.exception("Error occurred while adding vector layer to database")
        job.update(status=Status.FAILED)
        cleanup(job)
        return None

    # generate GeoParquet file for the vector layer
    if features:
        layer_id = features[0].properties.get("layer_id")
        if layer_id:
            static_dir = get_static_dir()

            # Generate GeoParquet file
            try:
                save_vector_layer_parquet(project_id, layer_id, gdf, static_dir)
                logger.info(f"Successfully generated parquet file for layer {layer_id}")
            except Exception:
                logger.exception(
                    f"Failed to generate parquet for layer {layer_id}, continuing without parquet"
                )

            # Generate FlatGeobuf file
            try:
                save_vector_layer_flatgeobuf(project_id, layer_id, gdf, static_dir)
                logger.info(
                    f"Successfully generated FlatGeobuf file for layer {layer_id}"
                )
            except Exception:
                logger.exception(
                    f"Failed to generate FlatGeobuf for layer {layer_id}, continuing without FlatGeobuf"
                )

    # remove uploaded file
    cleanup(job)

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)
