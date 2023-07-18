from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectUpdate
from app.tests.utils.team import create_random_team
from app.tests.utils.project import (
    create_random_project,
    random_harvest_date,
    random_planting_date,
)
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_team_description, random_team_name


def test_create_project_without_team(db: Session) -> None:
    """Verify new project without team association is created in database."""
    title = random_team_name()
    description = random_team_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
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


def test_create_project_with_team(db: Session) -> None:
    """Verify new project with team association is created in database."""
    title = random_team_name()
    description = random_team_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
    user = create_random_user(db)
    team = create_random_team(db, owner_id=user.id)
    project = create_random_project(
        db,
        title=title,
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        owner_id=user.id,
        team_id=team.id,
    )
    assert project.owner_id == user.id
    assert project.team_id == team.id


def test_get_project(db: Session) -> None:
    """Verify retrieving project by id returns correct project."""
    project = create_random_project(db)
    stored_project = crud.project.get(db=db, id=project.id)
    assert stored_project
    assert project.id == stored_project.id
    assert project.title == stored_project.title
    assert project.description == stored_project.description
    assert project.planting_date == stored_project.planting_date
    assert project.harvest_date == stored_project.harvest_date
    assert project.owner_id == stored_project.owner_id


def test_update_project(db: Session) -> None:
    """Verify update changes project attributes in database."""
    project = create_random_project(db)
    new_title = random_team_name()
    new_planting_date = random_planting_date()
    project_in_update = ProjectUpdate(title=new_title, planting_date=new_planting_date)
    project_update = crud.project.update(
        db=db, db_obj=project, obj_in=project_in_update
    )
    assert project.id == project_update.id
    assert new_title == project_update.title
    assert new_planting_date == project_update.planting_date
    assert project.planting_date == project_update.planting_date
    assert project.description == project_update.description
    assert project.owner_id == project_update.owner_id


def test_delete_project(db: Session) -> None:
    """Verify project is removed from database."""
    project = create_random_project(db)
    project_removed = crud.project.remove(db=db, id=project.id)
    project_after_remove = crud.project.get(db=db, id=project.id)
    assert project_after_remove is None
    assert project_removed.id == project.id
    assert project_removed.title == project.title
    assert project_removed.description == project.description
    assert project_removed.owner_id == project.owner_id
