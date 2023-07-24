from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Flight, status_code=status.HTTP_201_CREATED)
def create_flight(
    flight_in: schemas.FlightCreate,
    dataset_id: UUID,
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new flight for a project dataset."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    flight = crud.flight.create_with_dataset(
        db, obj_in=flight_in, dataset_id=dataset_id
    )
    return flight
