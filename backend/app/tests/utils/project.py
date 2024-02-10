from datetime import date
from uuid import UUID

from faker import Faker
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.project import ProjectCreate
from app.tests.utils.location import create_location, SampleLocation, SAMPLE_LOCATION
from app.tests.utils.user import create_user
from app.tests.utils.utils import random_team_name, random_team_description


faker = Faker()


def create_project(
    db: Session,
    title: str | None = None,
    description: str | None = None,
    planting_date: date | None = None,
    harvest_date: date | None = None,
    location: SampleLocation | None = None,
    owner_id: UUID | None = None,
    team_id: UUID | None = None,
) -> models.Project:
    """Create random project with no team association."""
    if owner_id is None:
        user = create_user(db)
        owner_id = user.id
    if title is None:
        title = random_team_name()
    if description is None:
        description = random_team_description()
    if planting_date is None:
        planting_date = random_planting_date()
    if harvest_date is None:
        harvest_date = random_harvest_date()
    if location is None:
        location = SAMPLE_LOCATION

    project_in = ProjectCreate(
        title=title,
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        location=location,
        team_id=team_id,
    )

    return crud.project.create_with_owner(
        db,
        obj_in=project_in,
        owner_id=owner_id,
    )["result"]


def random_harvest_date() -> date:
    """Create random harvest datetime between Sep. and Oct. of current year."""
    return faker.date_between(
        start_date=date(date.today().year, 9, 1),
        end_date=date(date.today().year, 10, 31),
    )


def random_planting_date() -> date:
    """Create random planting datetime between Apr. and May of current year."""
    return faker.date_between(
        start_date=date(date.today().year, 4, 1),
        end_date=date(date.today().year, 5, 31),
    )
