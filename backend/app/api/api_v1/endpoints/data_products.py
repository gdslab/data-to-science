import json
import logging
import os
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, List, Optional, Sequence, Union
from uuid import UUID, uuid4

import httpx
from geojson_pydantic import Feature, FeatureCollection, Polygon, MultiPolygon
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, utils
from app.core import security
from app.core.config import settings
from app.models.vector_layer import VectorLayer
from app.schemas.data_product_metadata import ZonalStatisticsProps
from app.tasks import (
    generate_zonal_statistics,
    generate_zonal_statistics_bulk,
    run_toolbox_process,
)
from app.utils.tusd.post_processing import process_data_product_uploaded_to_tusd


router = APIRouter()


logger = logging.getLogger("__name__")


def get_static_dir() -> str:
    if os.environ.get("RUNNING_TESTS") == "1":
        return settings.TEST_STATIC_DIR
    else:
        return settings.STATIC_DIR


def update_feature_properties(
    zonal_feature: Feature[Polygon, ZonalStatisticsProps]
) -> Feature[Polygon, ZonalStatisticsProps]:
    """Updates the Feature properties returned by the zonal statistics endpoint. The
    updated properties will include only the zonal statistics stats that were calculated
    and any original properties/attributes associated with the vector layer. If the
    vector layer has a property with the same name as one of the zonal statistic
    properties (e.g., "max"), the zonal statistic value will overwrite the original
    property value.

    Args:
        current_properties (dict): Current properties for a Feature.

    Returns:
        Feature[Polygon, ZonalStatisticsProps]: Feature with updated properties.
    """
    current_properties = zonal_feature.properties
    if "properties" in current_properties:
        original_properties = current_properties.pop("properties")
        id_prop = original_properties.get("id")
        # if one of the required properties exists in the original properties
        # of the vector layer, its value will be overwritten with by the
        # zonal statistic value calculated on D2S
        zonal_feature.properties = {
            **original_properties,
            **current_properties,
        }
        # if original props had an "id" property, rename it to "fid" for feature id
        if id_prop:
            zonal_feature.properties = {**zonal_feature.properties, "fid": id_prop}

    return zonal_feature


@router.get("/{data_product_id}", response_model=schemas.DataProduct)
def read_data_product(
    data_product_id: UUID,
    flight_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    upload_dir = get_static_dir()
    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )
    return data_product


@router.get("", response_model=Sequence[schemas.DataProduct])
def read_all_data_product(
    flight_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve all raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    upload_dir = get_static_dir()
    all_data_product = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir, user_id=current_user.id
    )
    return all_data_product


@router.put("/{data_product_id}", response_model=schemas.DataProduct)
def update_data_product_data_type(
    data_product_id: UUID,
    data_type_in: schemas.DataProductUpdateDataType,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: schemas.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    upload_dir = get_static_dir()
    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )
    # reject request if point cloud
    if data_product.data_type.lower() == "point_cloud":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change point cloud data type",
        )
    updated_data_product = crud.data_product.update_data_type(
        db, data_product_id=data_product_id, new_data_type=data_type_in.data_type
    )
    return updated_data_product


@router.delete("/{data_product_id}", response_model=schemas.DataProduct)
def deactivate_data_product(
    data_product_id: UUID,
    project: schemas.Project = Depends(deps.can_read_write_project),
    flight: schemas.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
        )
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    deactivated_data_product = crud.data_product.deactivate(
        db, data_product_id=data_product_id
    )
    if not deactivated_data_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to deactivate"
        )
    return deactivated_data_product


@router.post("/create_from_ext_storage", status_code=status.HTTP_202_ACCEPTED)
def process_data_product_from_external_storage(
    payload: schemas.RawDataMetadata,
    project_id: UUID,
    flight_id: UUID,
    db: Session = Depends(deps.get_db),
) -> Any:
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(payload.token, salt="rawdata")
    )
    # find job associated with task
    job = crud.job.get(db, id=payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find processing job",
        )
    # check if token is valid
    if not token_db_obj:
        job_update_in = schemas.JobUpdate(
            state="COMPLETED", status="FAILED", end_time=datetime.now()
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # check if user has write permission for project
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        job_update_in = schemas.JobUpdate(
            state="COMPLETED", status="FAILED", end_time=datetime.now()
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not isinstance(
        deps.can_read_write_project(project_id=project_id, db=db, current_user=user),
        models.Project,
    ):
        job_update_in = schemas.JobUpdate(
            state="COMPLETED", status="FAILED", end_time=datetime.now()
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to add data products to project",
        )

    # check if job failed
    if not payload.status.code:
        # update job table to show it failed
        job_update_in = schemas.JobUpdate(
            state="COMPLETED", status="FAILED", end_time=datetime.now()
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
    else:
        # iterate over each new data product and start post processing celery task
        for data_product in payload.products:
            if not os.path.exists(data_product.storage_path):
                job_update_in = schemas.JobUpdate(
                    state="COMPLETED", status="FAILED", end_time=datetime.now()
                )
                crud.job.update(db, db_obj=job, obj_in=job_update_in)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to locate data product on disk",
                )

        # copy report
        try:
            if os.path.exists(payload.report.storage_path) and os.path.join(
                get_static_dir(),
                "projects",
                str(project_id),
                "flights",
                str(flight_id),
                "raw_data",
                str(payload.report.raw_data_id),
            ):
                shutil.copyfile(
                    payload.report.storage_path,
                    os.path.join(
                        get_static_dir(),
                        "projects",
                        str(project_id),
                        "flights",
                        str(flight_id),
                        "raw_data",
                        str(payload.report.raw_data_id),
                        os.path.basename(payload.report.storage_path),
                    ),
                )
                # remove from network storage
                os.remove(payload.report.storage_path)
            else:
                logger.error(
                    "Report does not exist on network storage or raw data directory does not exist"
                )
        except Exception as e:
            logger.exception(f"Unable to copy report to raw data directory: {e}")

        # data products successfully derived from raw data
        job_update_in = schemas.JobUpdate(
            state="COMPLETED", status="SUCCESS", end_time=datetime.now()
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)

        # new jobs will be spawned for each data product as its processed further
        for data_product in payload.products:
            process_data_product_uploaded_to_tusd(
                db=db,
                user_id=user.id,
                storage_path=Path(data_product.storage_path),
                original_filename=Path(data_product.filename),
                dtype=data_product.data_type,
                project_id=project_id,
                flight_id=flight_id,
            )

    # remove token from database
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)


class ProcessingRequest(BaseModel):
    chm: bool
    exg: bool
    exgRed: int
    exgGreen: int
    exgBlue: int
    ndvi: bool
    ndviNIR: int
    ndviRed: int
    zonal: bool
    zonal_layer_id: str


@router.post("/{data_product_id}/tools", status_code=status.HTTP_202_ACCEPTED)
async def run_processing_tool(
    data_product_id: UUID,
    toolbox_in: ProcessingRequest,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # verify project and flight exist
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    # verify at least one processing tool was selected
    if (
        toolbox_in.exg is False
        and toolbox_in.ndvi is False
        and toolbox_in.zonal is False
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No product selected"
        )
    # get upload_dir
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = Path(settings.TEST_STATIC_DIR)
    else:
        upload_dir = Path(settings.STATIC_DIR)
    # find existing data product that will be used as input raster
    data_product: models.DataProduct | None = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        user_id=current_user.id,
        upload_dir=upload_dir,
    )
    # verify input raster exists and it is active
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # ndvi
    if toolbox_in.ndvi and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        ndvi_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="NDVI",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for ndvi tool output raster
        data_product_dir: Path = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(ndvi_data_product.id)
        )
        ndvi_filename: str = str(uuid4()) + ".tif"
        out_raster: Path = data_product_dir / ndvi_filename
        # run ndvi tool in background
        tool_params: dict = {
            "red_band_idx": toolbox_in.ndviRed,
            "nir_band_idx": toolbox_in.ndviNIR,
        }
        run_toolbox_process.apply_async(
            args=(
                "ndvi",
                data_product.filepath,
                str(out_raster),
                tool_params,
                ndvi_data_product.id,
                current_user.id,
            )
        )

    # exg
    if toolbox_in.exg and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        exg_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="ExG",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for exg tool output raster
        data_product_dir = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(exg_data_product.id)
        )
        exg_filename: str = str(uuid4()) + ".tif"
        out_raster = data_product_dir / exg_filename
        # run exg tool in background
        tool_params = {
            "red_band_idx": toolbox_in.exgRed,
            "green_band_idx": toolbox_in.exgGreen,
            "blue_band_idx": toolbox_in.exgBlue,
        }
        run_toolbox_process.apply_async(
            args=(
                "exg",
                data_product.filepath,
                str(out_raster),
                tool_params,
                exg_data_product.id,
                current_user.id,
            )
        )
    # zonal
    if toolbox_in.zonal and not os.environ.get("RUNNING_TESTS") == "1":
        features = crud.vector_layer.get_vector_layer_by_id(
            db, project_id=project.id, layer_id=toolbox_in.zonal_layer_id
        )
        feature_collection = FeatureCollection(
            **{"type": "FeatureCollection", "features": features}
        )
        generate_zonal_statistics_bulk.apply_async(
            args=(
                data_product.filepath,
                data_product_id,
                jsonable_encoder(feature_collection.__dict__),
            )
        )


@router.post(
    "/{data_product_id}/zonal_statistics",
    response_model=Feature[Union[Polygon, MultiPolygon], ZonalStatisticsProps],
)
async def create_zonal_statistics(
    data_product_id: UUID,
    zone_in: Feature,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )

    if not zone_in.properties:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zone feature missing properties",
        )

    vector_layer_feature_id = zone_in.properties.get("feature_id", None)

    # check if zonal stats already exist for this feature/data product
    if vector_layer_feature_id and utils.is_valid_uuid(vector_layer_feature_id):
        metadata = crud.data_product_metadata.get_by_data_product(
            db,
            category="zonal",
            data_product_id=data_product_id,
            vector_layer_feature_id=vector_layer_feature_id,
        )
        if len(metadata) == 1:
            # return previously generated zonal stats
            if (
                "stats" in metadata[0].properties
                and vector_layer_feature_id
                and utils.is_valid_uuid(vector_layer_feature_id)
            ):
                # query vector layer as GeoJSON feature
                vector_layer_query = select(func.ST_AsGeoJSON(VectorLayer)).where(
                    VectorLayer.vector_layer_feature_id == vector_layer_feature_id
                )
                with db as session:
                    vector_layer = session.execute(
                        vector_layer_query
                    ).scalar_one_or_none()
                    vector_layer_geojson_dict = json.loads(vector_layer)
                    # add zonal stats to geojson properties
                    vector_layer_geojson_dict["properties"] = {
                        **vector_layer_geojson_dict["properties"],
                        **metadata[0].properties["stats"],
                    }
                    return update_feature_properties(
                        Feature(**vector_layer_geojson_dict)
                    )

    # send request to celery task queue
    result = generate_zonal_statistics.apply_async(
        args=(data_product.filepath, {"features": [zone_in.model_dump()]})
    )

    # task returns list of zonal stats
    zonal_stats = result.get()

    if len(zonal_stats) != 1:
        # result either has no features or too many features
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to calculate zonal statistics",
        )

    if vector_layer_feature_id and utils.is_valid_uuid(vector_layer_feature_id):
        metadata_in = schemas.DataProductMetadataCreate(
            category="zonal",
            properties={"stats": zonal_stats[0]},
            vector_layer_feature_id=vector_layer_feature_id,
        )
        crud.data_product_metadata.create_with_data_product(
            db, obj_in=metadata_in, data_product_id=data_product.id
        )
        # query vector layer as GeoJSON feature
        vector_layer_query = select(func.ST_AsGeoJSON(VectorLayer)).where(
            VectorLayer.feature_id == vector_layer_feature_id
        )
        with db as session:
            vector_layer = session.execute(vector_layer_query).scalar_one_or_none()
            vector_layer_geojson_dict = json.loads(vector_layer)
            # add zonal stats to geojson properties
            vector_layer_geojson_dict["properties"] = {
                **vector_layer_geojson_dict["properties"],
                **zonal_stats[0],
            }

    return update_feature_properties(Feature(**vector_layer_geojson_dict))


@router.get(
    "/{data_product_id}/zonal_statistics",
    response_model=Optional[
        FeatureCollection[Feature[Union[Polygon, MultiPolygon], ZonalStatisticsProps]]
    ],
)
async def read_zonal_statistics(
    project_id: UUID,
    data_product_id: UUID,
    layer_id: Annotated[str, Query(max_length=12)],
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    def verify_stats_are_set(feature: Feature) -> bool:
        """Return False if any stat properties are missing or do not have value set.

        Args:
            feature (Feature): GeoJSON feature with stat properties.

        Returns:
            bool: True if stats are set, otherwise False.
        """
        required_props = ["max", "min", "std", "mean", "count", "median"]
        if not hasattr(feature, "properties") or not isinstance(
            feature.properties, dict
        ):
            return False
        return all(
            prop in feature.properties and feature.properties[prop] is not None
            for prop in required_props
        )

    # query vector layers as GeoJSON feature with zonal metadata in properties
    vector_layer_features = crud.vector_layer.get_vector_layer_by_id_with_metadata(
        db,
        project_id=project_id,
        layer_id=layer_id,
        data_product_id=data_product_id,
        metadata_category="zonal",
    )

    # verify stats and return None if stats missing or not set
    for feature in vector_layer_features:
        if not verify_stats_are_set(feature):
            return None

    return FeatureCollection(
        type="FeatureCollection",
        features=[
            update_feature_properties(feature) for feature in vector_layer_features
        ],
    )
