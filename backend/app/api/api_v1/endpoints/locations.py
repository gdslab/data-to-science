import json
import os
import shutil
from typing import Any
from uuid import uuid4

import geopandas as gpd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fiona.errors import DriverError
from geojson_pydantic import FeatureCollection, Polygon
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

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
    return json.loads(geojson_location)


@router.post(
    "/upload",
    response_model=FeatureCollection,
    status_code=status.HTTP_201_CREATED,
)
def upload_field_shapefile(
    files: UploadFile,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    temp_name = str(uuid4())
    upload_dir = f"{settings.UPLOAD_DIR}/{current_user.id}/locations/{temp_name}"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    zip_path = os.path.join(upload_dir, f"{temp_name}.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)
        try:
            geojson = json.loads(gpd.read_file(files.file).to_json())
            fc = FeatureCollection(**geojson)
            assert fc.type == "FeatureCollection"
            assert len(fc) == 2
            assert len(fc.features) > 0
            assert type(fc.features[0].geometry) == Polygon
        except DriverError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shapefile missing or missing required file",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to find shapefile in zip",
            )

    return geojson
