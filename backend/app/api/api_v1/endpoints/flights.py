import os
import shutil
from pathlib import Path
from typing import Any, List, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import normalize_sensor_value
from app.core.config import settings
from app.schemas.role import Role

router = APIRouter()


@router.post("", response_model=schemas.Flight, status_code=status.HTTP_201_CREATED)
def create_flight(
    flight_in: schemas.FlightCreate,
    project_id: UUID,
    project: schemas.Project = Depends(deps.can_read_write_project),
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
        db, project_uuid=project_id, member_id=pilot_id
    )
    if not pilot_is_project_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pilot must be project member",
        )
    # Normalize sensor value
    flight_in.sensor = normalize_sensor_value(flight_in.sensor)

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
    has_raster: bool = False,
    current_user: models.User = Depends(
        deps.get_current_approved_user_by_jwt_or_api_key
    ),
    project: schemas.Project = Depends(deps.can_read_project_with_jwt_or_api_key),
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
        has_raster=has_raster,
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


@router.put(
    "/{flight_id}/move_to_project/{destination_project_id}",
    response_model=schemas.Flight,
)
def update_flight_project(
    flight_id: UUID,
    destination_project_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_write_delete_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # check if user has permission to read/write to destination project
    project_membership = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=destination_project_id, member_id=current_user.id
    )
    # raise exception if not project member or member without owner/manager role
    if not project_membership or project_membership.role != Role.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be an owner of destination project",
        )

    # lock flight record if no active jobs, raise exception if active jobs
    jobs = crud.job.get_multi_by_flight(db, flight_id=flight_id, incomplete=True)
    if len(jobs) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must wait for outstanding jobs to finish",
        )
    with db as session:
        statement = (
            update(models.Flight)
            .values(read_only=True)
            .where(models.Flight.id == flight.id)
        )
        session.execute(statement)
        session.commit()

    # move flight static file directory (if exists) to destination project
    if os.environ.get("RUNNING_TESTS") == "1":
        static_dir = Path(settings.TEST_STATIC_DIR)
    else:
        static_dir = Path(settings.STATIC_DIR)

    src_directory = Path(
        static_dir / "projects" / str(flight.project_id) / "flights" / str(flight_id)
    )
    dst_directory = Path(
        static_dir
        / "projects"
        / str(destination_project_id)
        / "flights"
        / str(flight_id)
    )

    if os.path.exists(src_directory):
        # create "flights" directory in destination project directory if needed
        if not os.path.exists(dst_directory.parent):
            os.makedirs(dst_directory.parent)
        # copy flight directory to new destination
        shutil.move(src_directory, dst_directory)

    # unlock flight record
    with db as session:
        statement = (
            update(models.Flight)
            .values(read_only=False)
            .where(models.Flight.id == flight.id)
        )
        session.execute(statement)
        session.commit()

    # get updated flight
    updated_flight = crud.flight.change_flight_project(
        db, flight_id=flight_id, dst_project_id=destination_project_id
    )

    return updated_flight


@router.delete("/{flight_id}", response_model=schemas.Flight)
def deactivate_flight(
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    project: schemas.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Check if project is published
    if project.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate flight when project is published in a STAC catalog",
        )

    deactivated_flight = crud.flight.deactivate(db, flight_id=flight.id)
    if not deactivated_flight:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return deactivated_flight


@router.get("/{flight_id}/check_progress", response_model=List[schemas.Job])
def check_for_raw_data_jobs_in_progress(
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    jobs = crud.job.get_raw_data_jobs_by_flight_id(
        db, job_name="processing-raw-data", flight_id=flight_id, processing=True
    )
    return jobs
