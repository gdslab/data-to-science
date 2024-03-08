from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.location import Location
from app.models.project import Project
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: LocationCreate) -> Location:
        obj_in_data = jsonable_encoder(obj_in)
        location = Location(**obj_in_data)
        with db as session:
            session.add(location)
            session.commit()
            session.refresh(location)
        return location

    def get_geojson_location(self, db: Session, location_id: UUID) -> Location | None:
        statement = select(func.ST_AsGeoJSON(Location)).where(
            Location.id == location_id
        )
        with db as session:
            return session.scalar(statement)

    def update_location(
        self, db: Session, obj_in: LocationUpdate | dict[str, Any], location_id: UUID
    ) -> Location | None:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        stmt = update(Location).where(Location.id == location_id).values(update_data)
        with db as session:
            session.execute(stmt)
            session.commit()

        return self.get_geojson_location(db, location_id=location_id)


location = CRUDLocation(Location)
