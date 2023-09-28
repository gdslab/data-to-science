from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectUpdate
from app.tests.utils.flight import create_flight
from app.tests.utils.location import create_random_location
from app.tests.utils.team import create_random_team
from app.tests.utils.team_member import create_random_team_member
from app.tests.utils.project import (
    create_random_project,
    random_harvest_date,
    random_planting_date,
)
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_team_description, random_team_name


def test_create_project_without_team(db: Session) -> None:
    """Create new project with no team association."""
    title = random_team_name()
    description = random_team_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
    location = create_random_location(db)
    user = create_random_user(db)
    project = create_random_project(
        db,
        title=title,
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        location_id=location.id,
        owner_id=user.id,
    )
    assert project.title == title
    assert project.description == description
    assert project.planting_date == planting_date
    assert project.harvest_date == harvest_date
    assert project.location_id == location.id
    assert project.owner_id == user.id


def test_create_project_with_team(db: Session) -> None:
    """Create new project with a team association."""
    user = create_random_user(db)
    team = create_random_team(db, owner_id=user.id)
    project = create_random_project(
        db,
        owner_id=user.id,
        team_id=team.id,
    )
    assert project.owner_id == user.id
    assert project.team_id == team.id


def test_get_project_by_id(db: Session) -> None:
    """Find project by project id."""
    project = create_random_project(db)
    stored_project = crud.project.get(db, id=project.id)
    assert stored_project
    assert project.id == stored_project.id
    assert project.title == stored_project.title
    assert project.description == stored_project.description
    assert project.planting_date == stored_project.planting_date
    assert project.harvest_date == stored_project.harvest_date
    assert project.location_id == stored_project.location_id
    assert project.owner_id == stored_project.owner_id


def test_get_project_by_user_and_project_id(db: Session) -> None:
    """Find project by user id and project id."""
    user = create_random_user(db)
    project = create_random_project(db, owner_id=user.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project
    assert project.id == stored_project.id
    assert project.title == stored_project.title
    assert project.description == stored_project.description
    assert project.planting_date == stored_project.planting_date
    assert project.harvest_date == stored_project.harvest_date
    assert project.location_id == stored_project.location_id
    assert project.owner_id == stored_project.owner_id


def test_get_project_with_team_by_user_and_project_id(db: Session) -> None:
    """Find project with team members by project owner user id and project id."""
    user = create_random_user(db)
    team = create_random_team(db, owner_id=user.id)
    user2 = create_random_user(db)
    create_random_team_member(db, email=user2.email, team_id=team.id)
    project = create_random_project(db, owner_id=user.id, team_id=team.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project
    assert project.id == stored_project.id
    assert project.title == stored_project.title
    assert project.description == stored_project.description
    assert project.planting_date == stored_project.planting_date
    assert project.harvest_date == stored_project.harvest_date
    assert project.location_id == stored_project.location_id
    assert project.owner_id == stored_project.owner_id


def test_get_project_with_team_by_team_member_and_project_id(db: Session) -> None:
    """Find project with team members by team member id and project id."""
    user = create_random_user(db)
    team = create_random_team(db, owner_id=user.id)
    user2 = create_random_user(db)
    create_random_team_member(db, email=user2.email, team_id=team.id)
    project = create_random_project(db, owner_id=user.id, team_id=team.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user2.id
    )
    assert stored_project
    assert project.id == stored_project.id
    assert project.title == stored_project.title
    assert project.description == stored_project.description
    assert project.planting_date == stored_project.planting_date
    assert project.harvest_date == stored_project.harvest_date
    assert project.location_id == stored_project.location_id
    assert project.owner_id == stored_project.owner_id


def test_update_project(db: Session) -> None:
    """Update existing project in database."""
    project = create_random_project(db)
    new_title = random_team_name()
    new_planting_date = random_planting_date()
    project_in_update = ProjectUpdate(title=new_title, planting_date=new_planting_date)
    project_update = crud.project.update(db, db_obj=project, obj_in=project_in_update)
    assert project.id == project_update.id
    assert new_title == project_update.title
    assert new_planting_date == project_update.planting_date
    assert project.planting_date == project_update.planting_date
    assert project.description == project_update.description
    assert project.owner_id == project_update.owner_id


def test_read_project_flight_count(db: Session) -> None:
    user = create_random_user(db)
    project = create_random_project(db, owner_id=user.id)
    for _ in range(0, 5):
        create_flight(db, project_id=project.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project
    assert stored_project.flight_count == 5
