from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Dataset, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: schemas.DatasetCreate,
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new dataset in a project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    dataset = crud.dataset.create_with_project(
        db, obj_in=dataset_in, project_id=project_id
    )
    return dataset


@router.get("/", response_model=list[schemas.Dataset])
def read_datasets(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of datasets belonging to a project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    datasets = crud.dataset.get_project_dataset_list(
        db,
        project_id=project_id,
        skip=skip,
        limit=limit,
    )
    return datasets


@router.get("/{dataset_id}", response_model=schemas.Dataset)
def read_dataset(
    dataset_id: str,
    db: Session = Depends(deps.get_db),
    dataset: models.Dataset = Depends(deps.can_read_write_dataset),
) -> Any:
    """Retrieve dataset if current user has access to it."""
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    return dataset


@router.put("/{dataset_id}", response_model=schemas.Dataset)
def update_dataset(
    dataset_id: str,
    dataset_in: schemas.DatasetUpdate,
    dataset: models.Dataset = Depends(deps.can_read_write_dataset),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update dataset if current user is project owner or member."""
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    dataset = crud.dataset.update(db, db_obj=dataset, obj_in=dataset_in)
    return dataset
