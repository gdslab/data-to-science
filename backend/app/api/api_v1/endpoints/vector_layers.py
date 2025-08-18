import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Sequence, Union
from uuid import UUID

import geopandas as gpd
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import sanitize_file_name, get_tile_url_with_signed_payload
from app.core.config import settings
from app.tasks.upload_tasks import upload_vector_layer
from app.utils.job_manager import JobManager

router = APIRouter()


logger = logging.getLogger("__name__")


def cleanup_temp(temp_path: str) -> None:
    """Delete temp file or temp dir once no longer in use.

    Args:
        temp_path (str): Path to temporary file or directory.
    """
    if os.path.isfile(temp_path):
        os.remove(temp_path)
    elif os.path.isdir(temp_path):
        shutil.rmtree(temp_path)


def get_static_dir() -> str:
    """Returns current static directory path.

    Returns:
        str: Static directory path.
    """
    if os.environ.get("RUNNING_TESTS") == "1":
        return settings.TEST_STATIC_DIR
    else:
        return settings.STATIC_DIR


def get_project_tmp_dir(project_id: str) -> str:
    """Creates a tmp directory inside a project.

    Args:
        project_id (str): Unique project ID.

    Returns:
        str: File path for project tmp directory.
    """
    project_tmp_dir = os.path.join(get_static_dir(), "projects", project_id, "tmp")
    if not os.path.exists(project_tmp_dir):
        os.makedirs(project_tmp_dir)

    return project_tmp_dir


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_vector_layer(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Create temp file path for the uploaded vector file
    if file and file.filename:
        project_tmp_dir = get_project_tmp_dir(str(project.id))
        suffix = Path(file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, dir=project_tmp_dir, suffix=suffix
        )
        temp_file_path = temp_file.name
        temp_file.close()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read filename for uploaded map layer",
        )

    # Write uploaded vector file to disk at temp_file location
    try:
        with open(temp_file_path, "wb") as tmpf:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunk
                tmpf.write(chunk)
    except Exception:
        logger.exception("Unable to write uploaded file to disk")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save map layer",
        )

    # Create job for processing task
    job = JobManager(job_name="upload-vector-layer")
    try:
        job_db_obj = job.job
        assert job_db_obj is not None
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create job for processing task",
        )

    # Sanitize original file name
    original_file_name = sanitize_file_name(file.filename)

    # Start celery task for processing and adding uploaded vector file to database
    upload_vector_layer.apply_async(
        args=(temp_file_path, original_file_name, project.id, job.job_id)
    )


@router.get(
    "/{vector_layer_id}",
    response_model=schemas.vector_layer.VectorLayerFeatureCollection,
)
def read_vector_layer(
    vector_layer_id: UUID,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # Get layer id for vector layer
    vector_layer = crud.vector_layer.get(db, id=vector_layer_id)
    if not vector_layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector layer not found"
        )
    features = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=vector_layer.layer_id
    )
    if len(features) > 0:
        layer_id = "undefined"
        if features[0].properties and "layer_id" in features[0].properties.keys():
            layer_id = features[0].properties["layer_id"]
        feature_collection = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "preview_url": f"{settings.API_DOMAIN}{settings.STATIC_DIR}"
                f"/projects/{project.id}/vector/{layer_id}"
                f"/preview.png",
            },
        }
        return feature_collection


@router.get(
    "",
    response_model=Union[
        Sequence[schemas.vector_layer.VectorLayerPayload],
        Sequence[schemas.vector_layer.VectorLayerFeatureCollection],
    ],
)
def read_vector_layers(
    project: models.Project = Depends(deps.can_read_project_with_jwt_or_api_key),
    format: str = Query(None),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if format == "json":
        feature_collections = crud.vector_layer.get_multi_in_geojson_by_project(
            db, project_id=project.id
        )
        if len(feature_collections) > 0:
            final_feature_collections: list[
                schemas.vector_layer.VectorLayerFeatureCollection
            ] = []
        for features in feature_collections:
            layer_id = "undefined"
            if (
                len(features) > 0
                and features[0].properties
                and "layer_id" in features[0].properties.keys()
            ):
                layer_id = features[0].properties["layer_id"]
            feature_collection = {
                "type": "FeatureCollection",
                "features": features,
                "metadata": {
                    "preview_url": f"{settings.API_DOMAIN}{settings.STATIC_DIR}/projects/{project.id}/vector/{layer_id}/preview.png"
                },
            }
            final_feature_collections.append(
                schemas.vector_layer.VectorLayerFeatureCollection(**feature_collection)
            )
        return final_feature_collections
    else:
        # Vector layers associated with project id
        vector_layers = crud.vector_layer.get_multi_by_project(
            db, project_id=project.id
        )

        payload = [
            {
                "layer_id": layer[0],
                "layer_name": layer[1],
                "geom_type": layer[2],
                "signed_url": get_tile_url_with_signed_payload(layer[0]),
                "preview_url": get_preview_url(str(project.id), layer[0]),
            }
            for layer in vector_layers
        ]

        return JSONResponse(content=payload)


@router.get("/{layer_id}/download")
def download_vector_layer(
    layer_id: str,
    background_tasks: BackgroundTasks,
    format: str = Query("json", pattern="^(json|shp)$"),
    project: models.Project = Depends(deps.can_read_project_with_jwt_or_api_key),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Fetch GeoJSON features for vector layer
    features = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=layer_id
    )
    feature_collection = {
        "type": "FeatureCollection",
        "features": [feature.model_dump() for feature in features],
    }

    # Get original filename from first feature's properties
    layer_name = (
        features[0].properties.get("layer_name", "feature_collection")
        if features and features[0].properties
        else "feature_collection"
    )

    if format == "shp":
        # Convert GeoJSON dict to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features)

        # Create temporary directory for shapefile zip
        temp_dir = tempfile.mkdtemp()
        shp_file_path = os.path.join(temp_dir, Path(layer_name).stem + ".shp")

        try:
            # Export GeoDataFrame to shapefile
            gdf.to_file(shp_file_path, driver="ESRI Shapefile")

            # Zip exported shapefile
            zip_file_path = tempfile.NamedTemporaryFile(
                delete=False, suffix=".zip"
            ).name
            try:
                with zipfile.ZipFile(zip_file_path, "w") as zipf:
                    for file_name in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file_name)
                        zipf.write(file_path, arcname=file_name)
            except Exception:
                logger.exception("Failed to zip shapefile")
                cleanup_temp(zip_file_path)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to create shapefile",
                )
        except Exception:
            logger.exception("Failed to convert vector layer to shapefile")
            cleanup_temp(temp_dir)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create shapefile",
            )

        # Clean up temporary zip file and temporary directory after request finishes
        background_tasks.add_task(cleanup_temp, zip_file_path)
        background_tasks.add_task(cleanup_temp, temp_dir)

        return FileResponse(
            zip_file_path,
            media_type="application/zip",
            filename=Path(layer_name).stem + ".zip",
        )
    else:
        # Create FeatureCollection with GeoJSON features
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".geojson"
        )
        temp_file_path = temp_file.name

        try:
            json.dump(feature_collection, temp_file)
        except Exception:
            logger.exception("Failed to serialize feature collection")
            cleanup_temp(temp_file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create GeoJSON",
            )

        # Clean up temporary file after request finishes
        background_tasks.add_task(cleanup_temp, temp_file_path)

        return FileResponse(
            temp_file_path,
            media_type="application/geo+json",
            filename=Path(layer_name).stem + ".geojson",
        )


@router.delete("/{layer_id}", status_code=status.HTTP_200_OK)
def delete_vector_layer(
    layer_id: str,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Remove all vector layer records associated with layer_id
    crud.vector_layer.remove_layer_by_id(db, project_id=project.id, layer_id=layer_id)

    # Check if vector layer records associated with layer_id are still found
    removed_layer_id_features = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=layer_id
    )

    # Raise exception records were found
    if len(removed_layer_id_features) > 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to remove vector layer",
        )


def get_preview_url(project_id: str, layer_id: str) -> str:
    """Returns URL for vector layer preview image.

    Args:
        project_id (str): Unique project ID.
        layer_id (str): Unique layer ID.

    Returns:
        str: URL to vector layer preview image.
    """
    static_dir = get_static_dir()
    base_static_url = f"{settings.API_DOMAIN}{static_dir}"

    return f"{base_static_url}/projects/{project_id}/vector/{layer_id}/preview.png"
