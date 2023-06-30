from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.dataset import DatasetCreate


def create_random_dataset(
    db: Session, category: str, project_id: UUID
) -> models.Project:
    """Create random dataset for a project."""
    dataset_in = DatasetCreate(category=category)

    return crud.dataset.create_with_project(
        db=db, obj_in=dataset_in, project_id=project_id
    )
