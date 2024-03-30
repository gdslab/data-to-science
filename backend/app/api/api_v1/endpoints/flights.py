import os
from pathlib import Path
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
    # check if pilot exists and pilot is a project member
    pilot_id = flight_in.pilot_id
    pilot = crud.user.get(db, id=pilot_id)
    if not pilot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pilot not found"
        )
    pilot_is_project_member = crud.project_member.get_by_project_and_member_id(
        db, project_id=project_id, member_id=pilot_id
    )
    if not pilot_is_project_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pilot must be project member",
        )
    flight = crud.flight.create_with_project(
        db, obj_in=flight_in, project_id=project_id
    )
    return flight


@router.get("/{flight_id}", response_model=schemas.Flight)
def read_flight(
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve flight if current user has access to it."""
    return flight


@router.get("", response_model=Sequence[schemas.Flight])
def read_flights(
    request: Request,
    project_id: UUID,
    include_all: bool = True,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve flights associated with project user can access."""
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=current_user.id,
        include_all=include_all,
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
    flight = crud.flight.update(db, db_obj=flight, obj_in=flight_in)
    return flight


@router.delete("/{flight_id}", response_model=schemas.Flight)
def deactivate_flight(
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    deactivated_flight = crud.flight.deactivate(db, flight_id=flight.id)
    if not deactivated_flight:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return deactivated_flight
