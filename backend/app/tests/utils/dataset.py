from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.dataset import DatasetCreate
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


def create_random_dataset(
    db: Session, category: str, project_id: UUID | None = None
) -> models.Project:
    """Create random dataset for a project."""
    if project_id is None:
        project_owner = create_random_user(db=db)
        project = create_random_project(db=db, owner_id=project_owner.id)
        project_id = project.id
    dataset_in = DatasetCreate(category=category)

    return crud.dataset.create_with_project(
        db=db, obj_in=dataset_in, project_id=project_id
    )
