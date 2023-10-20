import json
import os
from uuid import UUID
from typing import Any

import geopandas as gpd
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile
from fiona.io import ZipMemoryFile
from geojson_pydantic import FeatureCollection, Polygon
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils.MapMaker import MapMaker

router = APIRouter()


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
    if request.client and request.client.host == "testclient":
        project_map_path = f"{settings.TEST_UPLOAD_DIR}/projects/{project.id}"
    else:
        project_map_path = f"{settings.UPLOAD_DIR}/projects/{project.id}"
    if not os.path.exists(project_map_path):
        os.makedirs(project_map_path)
    if os.path.exists(os.path.join(project_map_path, "preview_map.png")):
        os.remove(os.path.join(project_map_path, "preview_map.png"))
    coordinates = json.loads(location)["geometry"]["coordinates"]
    project_map = MapMaker(coordinates[0], project_map_path)
    project_map.save()

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
    geojson = {}
    try:
        with ZipMemoryFile(files.file.read()) as zmf:
            with zmf.open() as src:
                gdf = gpd.GeoDataFrame.from_features(src, crs=src.crs)
                geojson = json.loads(gdf.to_json())

                fc = FeatureCollection(**geojson)
                assert fc.type == "FeatureCollection"
                assert len(fc.features) > 0
                assert isinstance(fc.features[0].geometry, Polygon)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to unzip shapefile"
        )

    return geojson
