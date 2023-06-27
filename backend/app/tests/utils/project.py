from datetime import datetime
from random import uniform
from uuid import UUID

from faker import Faker
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.project import ProjectCreate
from app.tests.utils.group import create_random_group
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_group_name, random_group_description


faker = Faker()


def create_random_project_without_group(
    db: Session,
    title: str | None = None,
    description: str | None = None,
    location: dict | None = None,
    planting_date: datetime | None = None,
    harvest_date: datetime | None = None,
    owner_id: UUID | None = None,
) -> models.Project:
    """Create random project with no group association."""
    if owner_id is None:
        user = create_random_user(db)
        owner_id = user.id
    if title is None:
        title = random_group_name()
    if description is None:
        description = random_group_description()
    if location is None:
        location = random_geojson_location()
    if planting_date is None:
        planting_date = random_planting_date()
    if harvest_date is None:
        harvest_date = random_harvest_date()

    project_in = ProjectCreate(
        title=title,
        description=description,
        location=jsonable_encoder(location),
        planting_date=planting_date,
        harvest_date=harvest_date,
    )
    return crud.project.create_with_owner(db=db, obj_in=project_in, owner_id=owner_id)


def random_geojson_location() -> dict:
    """Create random GeoJSON point feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
                "coordinates": [
                    round(uniform(-180, 180), 5),
                    round(uniform(-90, 90), 5)
                ]
        },
        "properties": {
            "name": random_group_name()
        }
    } 


def random_harvest_date() -> datetime:
    """Create random harvest datetime between Sep. and Oct. of current year."""
    return faker.date_time_between_dates(
        datetime_start=datetime(datetime.today().year, 9, 1),
        datetime_end=datetime(datetime.today().year, 10, 31)
    )


def random_planting_date() -> datetime:
    """Create random planting datetime between Apr. and May of current year."""
    return faker.date_time_between_dates(
        datetime_start=datetime(datetime.today().year, 4, 1),
        datetime_end=datetime(datetime.today().year, 5, 31)
    )
