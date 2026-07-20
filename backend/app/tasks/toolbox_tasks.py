import math
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import geopandas as gpd
import rasterio
from celery.utils.log import get_task_logger
from geojson_pydantic import FeatureCollection
from rasterstats import zonal_stats
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.utils.job_manager import JobManager
from app.schemas.data_product import DataProductUpdate
from app.schemas.data_product_metadata import ZonalStatisticsProps
from app.schemas.job import Status
from app.utils.Toolbox import Toolbox

logger = get_task_logger(__name__)


def compute_zonal_statistics(
    input_raster: str, feature_collection: Dict[str, Any]
) -> List[ZonalStatisticsProps]:
    """Compute zonal statistics for a raster using a feature collection."""
    features = feature_collection.get("features", [])
    if len(features) == 0:
        return []

    with rasterio.open(input_raster) as src:
        # convert feature collection to dataframe and update crs to match src crs
        zones = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        zones = zones.to_crs(src.crs)
        minx, miny, maxx, maxy = zones.total_bounds
        # affine transformation
        affine = src.transform
        # create window for total bounding box of all zones in zone_feature
        # snap to whole pixels (floor offsets, ceil ends) so the window fully
        # covers the zones and its transform matches the read array
        window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, affine)
        col_off = math.floor(window.col_off)
        row_off = math.floor(window.row_off)
        width = math.ceil(window.col_off + window.width) - col_off
        height = math.ceil(window.row_off + window.height) - row_off
        window = rasterio.windows.Window(col_off, row_off, width, height)
        window_affine = rasterio.windows.transform(window, src.transform)
        # rasterstats only receives the array, so pass the source nodata explicitly
        # to silence its NodataWarning. Without a source nodata, fall back to
        # rasterstats' internal -999 sentinel when the band dtype can hold it,
        # else the dtype's maximum (-999 overflows unsigned integer bands)
        nodata = src.nodata
        if nodata is None:
            dtype_min, dtype_max = rasterio.dtypes.dtype_ranges[src.dtypes[0]]
            nodata = -999 if dtype_min <= -999 <= dtype_max else dtype_max
        # read first band contained within window into array
        # boundless read keeps the array aligned with window_affine when zones
        # extend past the raster's edge; out-of-raster pixels become nodata
        data = src.read(1, window=window, boundless=True, fill_value=nodata)
        # required zonal statistics
        required_stats = "count min max mean median std"
        # get stats for zone
        stats = zonal_stats(
            zones, data, affine=window_affine, stats=required_stats, nodata=nodata
        )

    return stats


@celery_app.task(name="calculate_zonal_statistics_task")
def calculate_zonal_statistics(
    input_raster: str, feature_collection: dict
) -> List[ZonalStatisticsProps]:
    """Generate zonal statistics for a raster using a feature collection."""
    job = JobManager(job_name="zonal")
    job.start()

    try:
        stats = compute_zonal_statistics(input_raster, feature_collection)
    except Exception:
        logger.exception("Unable to calculate zonal statistics")
        job.update(status=Status.FAILED)
        # re-raise so callers blocking on the result see a server error
        # rather than mistaking the failure for an empty result
        raise

    job.update(status=Status.SUCCESS)

    return stats


def _fail_job(job: JobManager, detail: str) -> None:
    """Mark a job as failed, preserving existing extra and recording a reason."""
    existing_extra = job.job.extra if job.job and job.job.extra else {}
    job.update(status=Status.FAILED, extra={**existing_extra, "detail": detail[:200]})


@celery_app.task(name="calculate_bulk_zonal_statistics_task")
def calculate_bulk_zonal_statistics(
    input_raster: str,
    data_product_id: UUID,
    feature_collection_dict: Dict[str, Any],
    job_id: Optional[UUID] = None,
) -> List[ZonalStatisticsProps]:
    # database session for updating data product and job tables
    db = next(get_db())

    # use job created by the tools endpoint, or create one if not provided
    if job_id:
        job = JobManager(job_id=job_id, db=db)
    else:
        job = JobManager(data_product_id=data_product_id, job_name="zonal", db=db)

    try:
        job.start()
        all_zonal_stats = compute_zonal_statistics(
            input_raster, feature_collection_dict
        )
    except Exception as e:
        logger.exception("Unable to complete tool process")
        # record only the exception class; str(e) can contain server paths
        _fail_job(job, f"Unable to calculate zonal statistics ({type(e).__name__})")
        return []

    try:
        # deserialize feature collection
        feature_collection: FeatureCollection = FeatureCollection(
            **feature_collection_dict
        )
        features = feature_collection.features
        # create metadata record for each zone
        for index, zstats in enumerate(all_zonal_stats):
            vector_layer_feature_id = features[index].properties["feature_id"]
            metadata_in = schemas.DataProductMetadataCreate(
                category="zonal",
                properties={"stats": zstats},
                vector_layer_feature_id=vector_layer_feature_id,
            )
            try:
                crud.data_product_metadata.create_with_data_product(
                    db, obj_in=metadata_in, data_product_id=data_product_id
                )
            except IntegrityError:
                # update existing metadata
                existing_metadata = crud.data_product_metadata.get_by_data_product(
                    db,
                    category="zonal",
                    data_product_id=data_product_id,
                    vector_layer_feature_id=vector_layer_feature_id,
                )
                if len(existing_metadata) == 1:
                    crud.data_product_metadata.update(
                        db,
                        db_obj=existing_metadata[0],
                        obj_in=schemas.DataProductMetadataUpdate(
                            properties={"stats": zstats}
                        ),
                    )
                else:
                    logger.exception("Unable to save zonal statistics")
                    _fail_job(job, "Unable to save zonal statistics")
                    return []
    except Exception as e:
        logger.exception("Unable to save zonal statistics")
        _fail_job(job, f"Unable to save zonal statistics ({type(e).__name__})")
        return []

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    return all_zonal_stats


@celery_app.task(name="run_toolbox_task")
def run_toolbox(
    tool_name: str,
    in_raster: str,
    out_raster: str,
    params: dict,
    new_data_product_id: UUID,
    user_id: UUID,
) -> None:
    """Celery task for a toolbox process.

    Args:
        tool_name (str): Name of tool to run.
        in_raster (str): Path to input raster.
        out_raster (str): Path for output raster.
        params (dict): Input parameters required by tool.
        new_data_product_id (UUID): Data product ID for output raster.
        user_id (UUID): ID of user creating the data product.
    """
    # database session for updating data product and job tables
    db = next(get_db())

    # create new job for tool process
    job = JobManager(data_product_id=new_data_product_id, job_name=tool_name)

    try:
        job.start()
        # run tool - a COG will also be produced for the tool output
        toolbox = Toolbox(in_raster, out_raster)
        out_raster, ip = toolbox.run(tool_name, params)
    except Exception:
        logger.exception("Unable to complete tool process")
        job.update(status=Status.FAILED)
        return None

    try:
        new_data_product = crud.data_product.get(db, id=new_data_product_id)
        if new_data_product and os.path.exists(out_raster) and ip:
            default_symbology = ip.get_default_symbology()
            # update data product record with stac properties
            crud.data_product.update(
                db,
                db_obj=new_data_product,
                obj_in=DataProductUpdate(
                    filepath=out_raster,
                    stac_properties=ip.stac_properties,
                    is_initial_processing_completed=True,
                ),
            )
            # create user style record with default symbology settings
            crud.user_style.create_with_data_product_and_user(
                db,
                obj_in=default_symbology,
                data_product_id=new_data_product.id,
                user_id=user_id,
            )
    except Exception:
        logger.exception("Unable to update data product and create user style")
        job.update(status=Status.FAILED)
        return None

    job.update(status=Status.SUCCESS)
