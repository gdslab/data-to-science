from typing import Any, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.post("", response_model=schemas.Flight, status_code=status.HTTP_201_CREATED)
def create_flight(
    flight_in: schemas.FlightCreate,
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new flight for a project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    flight = crud.flight.create_with_project(
        db, obj_in=flight_in, project_id=project_id
    )
    return flight


@router.get("/{flight_id}", response_model=schemas.Flight)
def read_flight(
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve flight if current user has access to it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    return flight


@router.get("", response_model=Sequence[schemas.Flight])
def read_flights(
    request: Request,
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve flights associated with project user can access."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if request.client and request.client.host == "testclient":
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir
    )
    return flights


@router.put("/{flight_id}", response_model=schemas.Flight)
def update_flight(
    flight_id: UUID,
    flight_in: schemas.FlightUpdate,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update flight if current user has access to it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    flight = crud.flight.update(db, db_obj=flight, obj_in=flight_in)
    return flight
