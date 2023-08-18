import os
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud
from app.schemas.raw_data import RawDataCreate
from app.tests.utils.flight import create_flight


def create_raw_data(
    db: Session, flight_id: UUID | None = None, filepath: str | None = None
):
    if not flight_id:
        flight = create_flight(db)
        flight_id = flight.id
    if not filepath:
        filepath = os.path.join(os.sep, "tmp", "myfile.tif")
    raw_data_in = RawDataCreate(filepath=filepath)
    return crud.raw_data.create_with_flight(db, obj_in=raw_data_in, flight_id=flight_id)
