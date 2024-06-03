import json
import logging
import os
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID, uuid4

from geojson_pydantic import Feature, FeatureCollection
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, utils
from app.tasks import generate_zonal_statistics, run_toolbox_process
from app.core.config import settings

router = APIRouter()


logger = logging.getLogger("__name__")


def get_data_product_dir(project_id: str, flight_id: str, data_product_id: str) -> Path:
    """Construct path to directory that will store uploaded data product.

    Args:
        project_id (str): Project ID associated with data product.
        flight_id (str): Flight ID associated with data product.
        data_product_id (str): ID for data product.

    Returns:
        Path: Full path to data product directory.
    """
    # get root static path
    if os.environ.get("RUNNING_TESTS") == "1":
        data_product_dir = Path(settings.TEST_STATIC_DIR)
    else:
        data_product_dir = Path(settings.STATIC_DIR)
    # construct path to project/flight/dataproduct
    data_product_dir = data_product_dir / "projects" / project_id
    data_product_dir = data_product_dir / "flights" / flight_id
    data_product_dir = data_product_dir / "data_products" / data_product_id
    # create folder for data product
    if not os.path.exists(data_product_dir):
        os.makedirs(data_product_dir)

    return data_product_dir


@router.get("/{data_product_id}", response_model=schemas.DataProduct)
def read_data_product(
    request: Request,
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
    return data_product


@router.get("", response_model=Sequence[schemas.DataProduct])
def read_all_data_product(
    request: Request,
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
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    all_data_product = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir, user_id=current_user.id
    )
    return all_data_product


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
    if not project.is_owner:
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


class ProcessingRequest(BaseModel):
    chm: bool
    exg: bool
    exgRed: int
    exgGreen: int
    exgBlue: int
    layer_id: UUID
    ndvi: bool
    ndviNIR: int
    ndviRed: int
    zonal: bool


@router.post("/{data_product_id}/tools", status_code=status.HTTP_202_ACCEPTED)
async def run_processing_tool(
    request: Request,
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
        data_product_dir = Path(settings.TEST_STATIC_DIR)
    else:
        data_product_dir = Path(settings.STATIC_DIR)
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
        data_product_dir: Path = get_data_product_dir(
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
        data_product_dir = get_data_product_dir(
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
            db, project_id=project.id, layer_id=toolbox_in.layer_id
        )
        feature_collection = FeatureCollection(
            **{"type": "FeatureCollection", "features": features}
        )
        run_toolbox_process.apply_async(
            args=(
                data_product.filepath,
                data_product_id,
                json.dumps(jsonable_encoder(feature_collection.__dict__)),
            )
        )


@router.post(
    "/{data_product_id}/zonal_statistics",
    response_model=list[schemas.data_product_metadata.ZonalStatistics],
)
async def get_zonal_statistics(
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

    vector_layer_id = zone_in.properties.get("id", None)

    # check if statistics already exist for this feature/data product
    if vector_layer_id and utils.is_valid_uuid(vector_layer_id):
        metadata = crud.data_product_metadata.get_by_data_product(
            db,
            category="zonal",
            data_product_id=data_product_id,
            vector_layer_id=vector_layer_id,
        )
        if len(metadata) == 1:
            if "stats" in metadata[0].properties:
                return [metadata[0].properties["stats"]]

    # serialize GeoJSON feature before passing to celery task
    feature_string = json.dumps(jsonable_encoder(zone_in.__dict__))

    # send request to celery task queue
    result = generate_zonal_statistics.apply_async(
        args=(data_product.filepath, feature_string)
    )

    # get zonal statistics from celery task once it finishes
    zonal_stats = result.get()

    # check if statistics were returned (returns array for each zone)
    if len(zonal_stats) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to calculate zonal statistics",
        )

    # if zonal feature has a id, create metadata record for it
    if vector_layer_id and utils.is_valid_uuid(vector_layer_id):
        # create metadata entry for this combination of data product and vector layer
        metadata_in = schemas.DataProductMetadataCreate(
            category="zonal",
            properties={"stats": zonal_stats[0]},
            vector_layer_id=vector_layer_id,
        )
        crud.data_product_metadata.create_with_data_product(
            db, obj_in=metadata_in, data_product_id=data_product.id
        )

    return zonal_stats
