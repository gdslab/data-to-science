from datetime import date
from uuid import UUID

from pydantic import BaseModel


# shared properties
class FlightBase(BaseModel):
    acquisition_date: date | None = None
    altitude: float | None = None
    side_overlap: float | None = None
    forward_overlap: float | None = None
    sensor: str | None = None
    platform: str | None = None


# properties to receive via API on creation
class FlightCreate(FlightBase):
    acquisition_date: date
    altitude: float
    side_overlap: float
    forward_overlap: float
    sensor: str
    platform: str
    pilot_id: UUID | None = None


# properties to receive via API on update
class FlightUpdate(FlightBase):
    pass


# properties shared by models stored in DB
class FlightInDBBase(FlightBase):
    id: UUID
    acquisition_date: date
    altitude: float
    side_overlap: float
    forward_overlap: float
    sensor: str
    platform: str

    project_id: UUID
    pilot_id: UUID | None = None

    class Config:
        orm_mode = True


# additional properties to return via API
class Flight(FlightInDBBase):
    pass


# additional properties stored in DB
class FlightInDB(FlightInDBBase):
    pass
