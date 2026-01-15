from datetime import datetime
from typing import Optional
from uuid import UUID

from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.models.indoor_project import IndoorProject
from app.schemas.indoor_project import IndoorProjectCreate
from app.tests.utils.user import create_user
from app.tests.utils.utils import random_team_name, random_team_description


def create_indoor_project(
    db: Session,
    title: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    owner_id: Optional[UUID] = None,
) -> IndoorProject:
    """
    Creates an indoor project.
    """
    if title is None:
        title = random_team_name()
    if description is None:
        description = random_team_description()
    if owner_id is None:
        owner_id = create_user(db).id

    indoor_project_in = IndoorProjectCreate(
        title=title, description=description, start_date=start_date, end_date=end_date
    )

    indoor_project = crud.indoor_project.create_with_owner(
        db, obj_in=indoor_project_in, owner_id=owner_id
    )

    return indoor_project
