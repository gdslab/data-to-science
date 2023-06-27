from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.tests.utils.group import create_random_group
from app.tests.utils.project import create_random_project, random_geojson_location, random_harvest_date, random_planting_date
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_group_description, random_group_name


def test_create_project_without_group(db: Session) -> None:
    title = random_group_name()
    description = random_group_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
    location = random_geojson_location()
    user = create_random_user(db)

    project = create_random_project(
        db, 
        title=title, 
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        owner_id=user.id,
    )
    assert project.title == title
    assert project.description == description
    assert project.planting_date == planting_date
    assert project.harvest_date == harvest_date
    assert project.owner_id == user.id


def test_create_project_with_group(db: Session) -> None:
    title = random_group_name()
    description = random_group_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
    location = random_geojson_location()
    user = create_random_user(db)
    group = create_random_group(db, owner_id=user.id)

    project = create_random_project(
        db, 
        title=title, 
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        owner_id=user.id,
        group_id=group.id,
    )
    assert project.title == title
    assert project.description == description
    assert project.planting_date == planting_date
    assert project.harvest_date == harvest_date
    assert project.owner_id == user.id
    assert project.group_id == group.id


def test_update_project(db: Session) -> None:
    project = create_random_project(db)
    new_title = random_group_name()
    new_planting_date = random_planting_date()
    project_in_update = ProjectUpdate(title=new_title, planting_date=new_planting_date)
    project_update = crud.project.update(db=db, db_obj=project, obj_in=project_in_update)
    assert project.id == project_update.id
    assert new_title == project_update.title
    assert new_planting_date == project_update.planting_date
    assert project.planting_date == project_update.planting_date
    assert project.description == project_update.description
    assert project.owner_id == project_update.owner_id


def test_delete_project(db: Session) -> None:
    project = create_random_project(db)
    project_removed = crud.group.remove(db=db, id=project.id)
    project_after_remove = crud.group.get(db=db, id=project.id)
    assert project_after_remove is None
    assert project_removed.id == project.id
    assert project_removed.title == project.title
    assert project_removed.description == project.description
    assert project_removed.owner_id == project.owner_id
