from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: LocationCreate,
    ) -> Location:
        obj_in_data = jsonable_encoder(obj_in)
        location = self.model(**obj_in_data)
        with db as session:
            session.add(location)
            session.commit()
            session.refresh(location)
        return location

    def get_geojson_location(self, db: Session, location_id: UUID) -> Location:
        statement = select(func.ST_AsGeoJSON(self.model)).where(
            self.model.id == location_id
        )
        with db as session:
            location = session.scalars(statement).one_or_none()
        return location


location = CRUDLocation(Location)
