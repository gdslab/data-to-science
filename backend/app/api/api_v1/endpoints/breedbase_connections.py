from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()
study_router = APIRouter()


@router.post(
    "", response_model=schemas.BreedbaseConnection, status_code=status.HTTP_201_CREATED
)
def create_breedbase_connection(
    project_id: UUID,
    breedbase_connection_in: schemas.BreedbaseConnectionCreate,
    project: models.Project = Depends(deps.can_read_write_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    breedbase_connection = crud.breedbase_connection.create_with_project(
        db, obj_in=breedbase_connection_in, project_id=project.id
    )
    return breedbase_connection


@router.get("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def read_breedbase_connection(
    breedbase_connection_id: UUID,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    return breedbase_connection


@study_router.get("/{study_id}", response_model=List[schemas.BreedbaseConnection])
def read_breedbase_connection_by_study_id(
    study_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    breedbase_connections = crud.breedbase_connection.get_by_study_id(
        db, study_id=study_id, user_id=current_user.id
    )
    return breedbase_connections


@router.get("", response_model=List[schemas.BreedbaseConnection])
def read_breedbase_connections(
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    breedbase_connections = crud.breedbase_connection.get_multi_by_project_id(
        db, project_id=project.id
    )
    return breedbase_connections


@router.put("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def update_breedbase_connection(
    breedbase_connection_id: UUID,
    breedbase_connection_in: schemas.BreedbaseConnectionUpdate,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project),
) -> Any:
    # Get breedbase connection
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    if not breedbase_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breedbase connection not found",
        )

    # Update breedbase connection
    breedbase_connection_updated = crud.breedbase_connection.update(
        db, db_obj=breedbase_connection, obj_in=breedbase_connection_in
    )
    return breedbase_connection_updated


@router.delete("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def delete_breedbase_connection(
    breedbase_connection_id: UUID,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project),
) -> Any:
    # Get breedbase connection
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    if not breedbase_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breedbase connection not found",
        )

    # Delete breedbase connection
    crud.breedbase_connection.remove(db, id=breedbase_connection_id)
    return breedbase_connection
