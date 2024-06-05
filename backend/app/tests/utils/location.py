from typing import Dict, TypedDict

from geojson_pydantic import Feature, Polygon
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.location import LocationCreate
from app.tests.utils.utils import get_geojson_feature_collection


def create_location(db: Session) -> Feature[Polygon, Dict]:
    """Create random location."""
    feature_collection = get_geojson_feature_collection("polygon")["geojson"]
    feature = feature_collection["features"][0]
    location_in = LocationCreate(**feature)
    return crud.location.create_with_geojson(db, obj_in=location_in)
