import json
from typing import Any, Dict
from uuid import UUID

from geojson_pydantic import Feature, Polygon
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.location import Location
from app.models.project import Project
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def create_with_geojson(
        self, db: Session, *, obj_in: LocationCreate
    ) -> Feature[Polygon, Dict] | None:
        # GeoJSON Feature
        feature = obj_in
        # Get geometry from GeoJSON Feature (not interested in props)
        geometry = feature.geometry.__dict__
        # Serialize geometry for ST_GeomFromGeoJSON function
        geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))
        location = Location(geom=geom)
        with db as session:
            session.add(location)
            session.commit()
            session.refresh(location)

        return self.get_geojson_location(db, location_id=location.id)

    def get_geojson_location(
        self, db: Session, location_id: UUID
    ) -> Feature[Polygon, Dict] | None:
        statement = select(
            func.ST_AsGeoJSON(Location),
            func.ST_X(func.ST_Centroid(Location.geom)).label("center_x"),
            func.ST_Y(func.ST_Centroid(Location.geom)).label("center_y"),
        ).where(Location.id == location_id)

        with db as session:
            location = session.execute(statement).one_or_none()
            if location is None:
                return None

            location_dict = json.loads(location[0])
            location_dict["properties"].update(
                {"center_x": location[1], "center_y": location[2]}
            )
            return Feature[Polygon, Dict](**location_dict)

    def update_location(
        self, db: Session, obj_in: LocationUpdate | dict[str, Any], location_id: UUID
    ) -> Feature[Polygon, Dict] | None:
        # GeoJSON Feature
        feature = obj_in
        # Get geometry from GeoJSON Feature (not interested in props)
        geometry = feature.geometry.__dict__
        # Serialize geometry for ST_GeomFromGeoJSON function
        geom = func.ST_GeomFromGeoJSON(json.dumps(geometry))

        statement = update(Location).where(Location.id == location_id).values(geom=geom)
        with db as session:
            session.execute(statement)
            session.commit()

        return self.get_geojson_location(db, location_id=location_id)


location = CRUDLocation(Location)
