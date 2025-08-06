import json
import logging
import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, Optional, Sequence, Union
from urllib.parse import urlparse, parse_qs
from uuid import UUID, uuid4

import segno
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from geojson_pydantic import Feature, FeatureCollection, Polygon, MultiPolygon
from pydantic import BaseModel, UUID4
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, utils
from app.core import security
from app.core.config import settings
from app.models.vector_layer import VectorLayer
from app.schemas.data_product_metadata import ZonalStatisticsProps
from app.schemas.job import Status
from app.schemas.role import Role
from app.tasks.toolbox_tasks import (
    calculate_zonal_statistics,
    calculate_bulk_zonal_statistics,
    run_toolbox,
)
from app.schemas.shortened_url import ShortenedUrlApiResponse, UrlPayload
from app.utils.job_manager import JobManager
from app.utils.tusd.post_processing import process_data_product_uploaded_to_tusd


router = APIRouter()


logger = logging.getLogger("__name__")


def get_static_dir() -> str:
    if os.environ.get("RUNNING_TESTS") == "1":
        return settings.TEST_STATIC_DIR
    else:
        return settings.STATIC_DIR


def update_feature_properties(
    zonal_feature: Feature[Polygon, ZonalStatisticsProps],
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


@router.post("/{data_product_id}/utils/shorten")
def get_shortened_url(
    data_product_id: UUID,
    payload: UrlPayload,
    qrcode: bool = False,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    flight: models.Flight = Depends(deps.can_read_flight),
) -> Union[ShortenedUrlApiResponse, Any]:
    """Generates shortened URL for share URL received in payload.

    Args:
        data_product_id (UUID): ID of data product being shared.
        payload (UrlPayload): Share URL to be shortened.
        qrcode (bool, optional): Whether to generate a QR code. Defaults to False.
        current_user (models.User, optional): Current logged in user. Defaults to Depends(deps.get_current_approved_user).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).
        flight (models.Flight, optional): Flight associated with data product. Defaults to Depends(deps.can_read_flight).

    Raises:
        HTTPException: Raised if unable to parse share URL in payload.
        HTTPException: Raised if data product ID and file ID in share URL do not match.
        HTTPException: Raised if we fail to create/fetch shortened URL.

    Returns:
        ShortenedUrlApiResponse: Shortened URL.
    """
    # Get share url from payload
    share_url = payload.url

    # Parse out data product id from the share url
    try:
        parsed_url = urlparse(share_url)
        query_params = parse_qs(parsed_url.query)
        file_id = query_params.get("file_id", [None])[0]
    except Exception as e:
        logger.error(f"Unable to parse URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL"
        )

    # Raise exception if the data product id in the url
    # does not match the data product id in the share url
    if str(data_product_id) != file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data product ID mismatch"
        )

    # Create shortened url or fetch existing shortened url
    shortened_url = crud.shortened_url.create_with_unique_short_id(
        db, original_url=share_url, user_id=current_user.id
    )
    if not shortened_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to shorten URL"
        )
    url = f"{settings.SHORTENED_URL_BASE}/{shortened_url.short_id}"

    if qrcode:
        qrcode_image = segno.make(url)
        buffer = BytesIO()
        qrcode_image.save(buffer, kind="png", scale=10)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")
    else:
        return schemas.ShortenedUrlApiResponse(shortened_url=url)


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


@router.put("/{data_product_id}/bands", response_model=schemas.DataProduct)
def update_data_product_bands(
    data_product_id: UUID4,
    data_product_bands_in: schemas.DataProductBands,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: schemas.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Raise exception if flight is not found
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )

    # Get upload directory
    upload_dir = get_static_dir()

    # Get data product
    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )

    # Check if data product exists
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    # Check if data product STAC metadata exists
    if not data_product.stac_properties:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data product has no STAC metadata",
        )

    # Verify and update band metadata
    current_metadata = data_product.stac_properties
    current_eo_metadata = current_metadata.get("eo", [])
    current_band_names = {band["name"]: band for band in current_eo_metadata}
    for band_in in data_product_bands_in.bands:
        if band_in.name not in current_band_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Band not found"
            )
        # Update band description
        current_band_names[band_in.name]["description"] = band_in.description

    # Update metadata
    current_metadata["eo"] = list(current_band_names.values())

    # Update data product bands
    updated_data_product = crud.data_product.update_bands(
        db,
        data_product_id=data_product_id,
        updated_metadata=current_metadata,
    )

    return updated_data_product


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
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    if not data_type_in.data_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data type is required"
        )

    # reject request if point cloud or panoramic
    if (
        data_product.data_type.lower() == "point_cloud"
        or data_product.data_type.lower() == "panoramic"
    ):
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
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if project.role != Role.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
        )

    # Check if project is published
    if project.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate data product when project is published in a STAC catalog",
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
    try:
        job = JobManager(job_id=payload.job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find processing job",
        )
    # check if token is valid
    if not token_db_obj:
        job.update(status=Status.FAILED)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # check if user has write permission for project
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        job.update(status=Status.FAILED)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not isinstance(
        deps.can_read_write_project(project_id=project_id, db=db, current_user=user),
        models.Project,
    ):
        job.update(status=Status.FAILED)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to add data products to project",
        )

    # check if job failed
    if not payload.status.code:
        # update job table to show it failed
        job.update(status=Status.FAILED)
    else:
        # iterate over each new data product and start post processing celery task
        for data_product in payload.products:
            if not os.path.exists(data_product.storage_path):
                job.update(status=Status.FAILED)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to locate data product on disk",
                )

        # copy report
        try:
            if (
                payload.report
                and os.path.exists(payload.report.storage_path)
                and os.path.join(
                    get_static_dir(),
                    "projects",
                    str(project_id),
                    "flights",
                    str(flight_id),
                    "raw_data",
                    str(payload.report.raw_data_id),
                )
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
            else:
                logger.error(
                    "Report does not exist on network storage or raw data directory does not exist"
                )
        except Exception as e:
            logger.exception(f"Unable to copy report to raw data directory: {e}")

        # data products successfully derived from raw data
        job.update(status=Status.SUCCESS)

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
                project_to_utm=True,
            )

    # remove token from database
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)


@router.post("/{data_product_id}/tools", status_code=status.HTTP_202_ACCEPTED)
async def run_processing_tool(
    data_product_id: UUID,
    toolbox_in: schemas.ProcessingRequest,
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
        toolbox_in.chm is False
        and toolbox_in.dtm is False
        and toolbox_in.exg is False
        and toolbox_in.hillshade is False
        and toolbox_in.ndvi is False
        and toolbox_in.vari is False
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
        upload_dir=str(upload_dir),
    )
    # verify input raster exists and it is active
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    # chm
    if toolbox_in.chm and not os.environ.get("RUNNING_TESTS") == "1":
        # check if dem_id is set
        if not toolbox_in.dem_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DEM data product ID is required",
            )
        # create new data product record
        chm_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="CHM",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for chm tool output raster
        data_product_dir = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(chm_data_product.id)
        )
        chm_filename: str = str(uuid4()) + ".tif"
        out_raster = data_product_dir / chm_filename
        # get fullpath to dem data product
        dem_data_product = crud.data_product.get_single_by_id(
            db,
            data_product_id=toolbox_in.dem_id,
            user_id=current_user.id,
            upload_dir=str(upload_dir),
        )
        if not dem_data_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DEM data product not found",
            )
        # run chm tool in background
        tool_params = {
            "dem_input": dem_data_product.filepath,
            "chm_resolution": toolbox_in.chmResolution,
            "chm_percentile": toolbox_in.chmPercentile,
        }
        run_toolbox.apply_async(
            args=(
                "chm",
                data_product.filepath,
                str(out_raster),
                tool_params,
                chm_data_product.id,
                current_user.id,
            )
        )

    # dtm
    if toolbox_in.dtm and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        dtm_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="DTM",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for dtm tool output raster
        data_product_dir = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(dtm_data_product.id)
        )
        dtm_filename: str = str(uuid4()) + ".tif"
        out_raster = data_product_dir / dtm_filename
        # run dtm tool in background
        tool_params = {
            "dtm_resolution": toolbox_in.dtmResolution,
            "dtm_rigidness": toolbox_in.dtmRigidness,
        }
        run_toolbox.apply_async(
            args=(
                "dtm",
                data_product.filepath,
                str(out_raster),
                tool_params,
                dtm_data_product.id,
                current_user.id,
            )
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
        run_toolbox.apply_async(
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
        run_toolbox.apply_async(
            args=(
                "exg",
                data_product.filepath,
                str(out_raster),
                tool_params,
                exg_data_product.id,
                current_user.id,
            )
        )

    # hillshade
    if toolbox_in.hillshade and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        hillshade_data_product: models.DataProduct = (
            crud.data_product.create_with_flight(
                db,
                schemas.DataProductCreate(
                    data_type="Hillshade",
                    filepath="null",
                    original_filename=data_product.original_filename,
                ),
                flight_id=flight.id,
            )
        )
        # get path for hillshade tool output raster
        data_product_dir = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(hillshade_data_product.id)
        )
        hillshade_filename: str = str(uuid4()) + ".tif"
        out_raster = data_product_dir / hillshade_filename
        # run hillshade tool in background
        run_toolbox.apply_async(
            args=(
                "hillshade",
                data_product.filepath,
                str(out_raster),
                {},
                hillshade_data_product.id,
                current_user.id,
            )
        )

    # vari
    if toolbox_in.vari and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        vari_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="VARI",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for vari tool output raster
        data_product_dir = utils.get_data_product_dir(
            str(project.id), str(flight.id), str(vari_data_product.id)
        )
        vari_filename: str = str(uuid4()) + ".tif"
        out_raster = data_product_dir / vari_filename
        # run vari tool in background
        tool_params = {
            "red_band_idx": toolbox_in.variRed,
            "green_band_idx": toolbox_in.variGreen,
            "blue_band_idx": toolbox_in.variBlue,
        }
        run_toolbox.apply_async(
            args=(
                "vari",
                data_product.filepath,
                str(out_raster),
                tool_params,
                vari_data_product.id,
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
        calculate_bulk_zonal_statistics.apply_async(
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

    # required zonal stats
    required_stats = {"count", "min", "max", "mean", "median", "std"}

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
                # if all required stats are present
                if all(
                    key in metadata[0].properties["stats"] for key in required_stats
                ):
                    # query vector layer as GeoJSON feature
                    vector_layer_query = select(func.ST_AsGeoJSON(VectorLayer)).where(
                        VectorLayer.feature_id == vector_layer_feature_id
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
                else:
                    # missing one or more stats, remove record and recalculate
                    crud.data_product_metadata.remove(db, id=metadata[0].id)

    # send request to celery task queue
    result = calculate_zonal_statistics.apply_async(
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
