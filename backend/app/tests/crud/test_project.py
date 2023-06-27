from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.tests.utils.project import create_random_project_without_group, random_geojson_location, random_harvest_date, random_planting_date
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_group_description, random_group_name


# def test_create_project_without_group(db: Session) -> None:
#     title = random_group_name()
#     description = random_group_description()
#     planting_date = random_planting_date()
#     harvest_date = random_harvest_date()
#     location = random_geojson_location()
#     user = create_random_user(db)

#     project = create_random_project_without_group(
#         db, 
#         title=title, 
#         description=description,
#         planting_date=planting_date,
#         harvest_date=harvest_date,
#         owner_id=user.id,
#     )
#     assert project.title == title
#     assert project.description == description
#     assert project.planting_date == planting_date
#     assert project.harvest_date == harvest_date
#     assert project.owner_id == user.id
