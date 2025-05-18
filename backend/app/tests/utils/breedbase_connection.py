from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud
from app.models.breedbase_connection import BreedbaseConnection
from app.schemas import BreedbaseConnectionCreate


def create_breedbase_connection(
    db: Session,
    project_id: UUID,
    base_url: Optional[str] = None,
    trial_id: Optional[str] = None,
) -> BreedbaseConnection:
    """Create a breedbase connection."""
    if base_url is None:
        base_url = "https://example.com"
    if trial_id is None:
        trial_id = "1234567890"

    breedbase_connection_in = BreedbaseConnectionCreate(
        base_url=base_url,
        trial_id=trial_id,
    )

    return crud.breedbase_connection.create_with_project(
        db, obj_in=breedbase_connection_in, project_id=project_id
    )
