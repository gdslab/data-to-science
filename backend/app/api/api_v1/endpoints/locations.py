import logging
import json
import os
import shutil
import tempfile
from pathlib import Path
from uuid import UUID
from typing import Any
from zipfile import ZipFile

import fiona
import geopandas as gpd
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile
from fiona.errors import DriverError
from fiona.io import ZipMemoryFile
from geojson_pydantic import FeatureCollection, Polygon
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import create_project_field_preview
from app.core.config import settings
from app.utils.MapMaker import MapMaker

router = APIRouter()


logger = logging.getLogger("__name__")


REQUIRED_SHP_PARTS = [".dbf", ".shp", ".shx"]


@router.post(
    "",
    response_model=schemas.location.PolygonGeoJSONFeature,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    location_in: schemas.LocationCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new location."""
    location = crud.location.create_with_owner(db, obj_in=location_in)
    geojson_location = crud.location.get_geojson_location(db, location_id=location.id)
    if not geojson_location:
        raise HTTPException(
            status_code=status.HTTP_404_BAD_REQUEST, detail="Location not created"
        )
    return json.loads(geojson_location)


@router.put(
    "/{project_id}/{location_id}", response_model=schemas.location.PolygonGeoJSONFeature
)
def update_location(
    request: Request,
    location_id: UUID,
    location_in: schemas.LocationUpdate,
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    location = crud.location.update_location(
        db=db, obj_in=location_in, location_id=location_id
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    # Update project map preview
    coordinates = json.loads(location)["geometry"]["coordinates"]
    create_project_field_preview(request, project_id, coordinates)

    return json.loads(location)


@router.post(
    "/upload",
    response_model=FeatureCollection,
    status_code=status.HTTP_200_OK,
)
def upload_field_shapefile(
    request: Request,
    files: UploadFile,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Handles zipped shapefile upload and converts to geojson format."""
    geojson = {}
    uploaded_file = files.file.read()
    try:
        # attempt to directly access uploaded shapefile from memory
        with ZipMemoryFile(uploaded_file) as zmf:
            with zmf.open() as src:
                geojson = shapefile_to_geojson(src)
    except DriverError as e:
        logger.error(e)
        try:
            # attempt temporarily writing zip to disk and accessing shapefile
            with tempfile.TemporaryDirectory() as tmpdirname:
                with tempfile.NamedTemporaryFile(dir=tmpdirname) as tmpf:
                    with open(tmpf.name, "wb") as buffer:
                        buffer.write(uploaded_file)
                    with ZipFile(tmpf.name) as zip_contents:
                        if is_shapefile(zip_contents.namelist()):
                            shp_path = extract_shapefile_parts(zip_contents, tmpdirname)
                            if shp_path:
                                with fiona.open(shp_path) as src:
                                    geojson = shapefile_to_geojson(src)
                            else:
                                raise ValueError("Unable to find .shp in zip")
                        else:
                            raise ValueError("Missing required shapefile parts in zip")
        except ValueError as e:
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable process shapefile",
            )
    if not geojson:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable process shapefile",
        )

    return geojson


def shapefile_to_geojson(src: fiona.model.Feature) -> dict:
    """Loads shapefile with geopandas and returns GeoJSON object.

    Args:
        src (fiona.model.Feature): Shapefile object.

    Returns:
        dict: GeoJSON object.
    """
    gdf = gpd.GeoDataFrame.from_features(src, crs=src.crs)
    geojson = json.loads(gdf.to_json(to_wgs84=True))

    fc = FeatureCollection(**geojson)
    assert fc.type == "FeatureCollection"
    assert len(fc.features) > 0
    assert isinstance(fc.features[0].geometry, Polygon)

    return geojson


def is_shapefile(zip_contents: list) -> bool:
    """Checks if zip archive contains necessary shapefile parts in its root dir.

    Args:
        zip_contents (list): Contents of zip's root directory.

    Returns:
        bool: True if required shapefile parts were present in archive.
    """
    zip_rootdir_extensions = [Path(zfile).suffix for zfile in zip_contents]
    for required_file in REQUIRED_SHP_PARTS:
        if required_file not in zip_rootdir_extensions:
            return False
    return True


def extract_shapefile_parts(zip: ZipFile, tmpdirname: str) -> str:
    """Extracts the required shapefile parts from a zip archive. If a projection
    file (.prj) is available, it is also extracted.

    Args:
        zip (ZipFile): Zip archive containing shapefile.
        tmpdirname (str): Temporary directory for zip.

    Returns:
        str: Path to .shp file.
    """
    zip_contents = zip.namelist()
    shp_path = ""
    for required_file in REQUIRED_SHP_PARTS:
        for zip_file in zip_contents:
            zip_file_ext = Path(zip_file).suffix
            if zip_file_ext == required_file or zip_file_ext == ".prj":
                zip.extract(zip_file, path=tmpdirname)
                if zip_file_ext == ".shp":
                    shp_path = os.path.join(tmpdirname, zip_file)
    return shp_path
