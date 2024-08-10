from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.data_product import DataProduct


# shared properties
class FlightBase(BaseModel):
    name: str | None = None
    acquisition_date: date | None = None
    altitude: float | None = None
    side_overlap: float | None = None
    forward_overlap: float | None = None
    sensor: str | None = None
    platform: str | None = None
    is_active: bool = True
    pilot_id: UUID | None = None


# properties to receive via API on creation
class FlightCreate(FlightBase):
    acquisition_date: date
    altitude: float
    side_overlap: float
    forward_overlap: float
    sensor: str
    platform: str
    pilot_id: UUID


# properties to receive via API on update
class FlightUpdate(FlightBase):
    pass


# properties shared by models stored in DB
class FlightInDBBase(FlightBase, from_attributes=True):
    id: UUID
    acquisition_date: date
    altitude: float
    side_overlap: float
    forward_overlap: float
    sensor: str
    platform: str
    is_active: bool
    deactivated_at: datetime | None = None
    read_only: bool

    project_id: UUID
    pilot_id: UUID | None = None


# additional properties to return via API
class Flight(FlightInDBBase):
    data_products: list[DataProduct]


# additional properties stored in DB
class FlightInDB(FlightInDBBase):
    pass
