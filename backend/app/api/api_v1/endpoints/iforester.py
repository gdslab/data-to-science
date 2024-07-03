from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.post("", response_model=schemas.IForester, status_code=status.HTTP_201_CREATED)
def create_iforester(
    iforester_in: schemas.IForesterCreate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.create_iforester(
        db, iforester_in=iforester_in, project_id=project.id
    )
    return iforester


@router.get(
    "/{iforester_id}", response_model=schemas.IForester, status_code=status.HTTP_200_OK
)
def read_iforester(
    iforester_id: UUID4,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester_id, project_id=project.id
    )
    return iforester


@router.put(
    "/{iforester_id}", response_model=schemas.IForester, status_code=status.HTTP_200_OK
)
def update_iforester(
    iforester_id: UUID4,
    iforester_in: schemas.IForesterUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.update_iforester_by_id(
        db, iforester_in=iforester_in, iforester_id=iforester_id, project_id=project.id
    )
    return iforester


@router.delete(
    "/{iforester_id}", response_model=schemas.IForester, status_code=status.HTTP_200_OK
)
def delete_iforester(
    iforester_id: UUID4,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.remove_iforester_by_id(
        db, iforester_id=iforester_id, project_id=project.id
    )
    return iforester
