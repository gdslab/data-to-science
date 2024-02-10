from datetime import datetime

from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.location import create_location, SAMPLE_LOCATION
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.project import (
    create_project,
    random_harvest_date,
    random_planting_date,
)
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user
from app.tests.utils.utils import random_team_description, random_team_name


def test_create_project_without_team(db: Session) -> None:
    title = random_team_name()
    description = random_team_description()
    planting_date = random_planting_date()
    harvest_date = random_harvest_date()
    user = create_user(db)
    project = create_project(
        db,
        title=title,
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        location=SAMPLE_LOCATION,
        owner_id=user.id,
    )
    assert project.title == title
    assert project.description == description
    assert project.planting_date == planting_date
    assert project.harvest_date == harvest_date
    assert project.location_id
    assert project.owner_id == user.id


def test_create_project_with_team(db: Session) -> None:
    user = create_user(db)
    team = create_team(db, owner_id=user.id)
    project = create_project(
        db,
        owner_id=user.id,
        team_id=team.id,
    )
    assert project.owner_id == user.id
    assert project.team_id == team.id


def test_get_project_by_id(db: Session) -> None:
    project = create_project(db)
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
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert project.id == stored_project["result"].id
    assert project.title == stored_project["result"].title
    assert project.description == stored_project["result"].description
    assert project.planting_date == stored_project["result"].planting_date
    assert project.harvest_date == stored_project["result"].harvest_date
    assert project.location_id == stored_project["result"].location_id
    assert project.owner_id == stored_project["result"].owner_id


def test_get_project_with_team_by_user_and_project_id(db: Session) -> None:
    user = create_user(db)
    team = create_team(db, owner_id=user.id)
    user2 = create_user(db)
    create_team_member(db, email=user2.email, team_id=team.id)
    project = create_project(db, owner_id=user.id, team_id=team.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert project.id == stored_project["result"].id
    assert project.title == stored_project["result"].title
    assert project.description == stored_project["result"].description
    assert project.planting_date == stored_project["result"].planting_date
    assert project.harvest_date == stored_project["result"].harvest_date
    assert project.location_id == stored_project["result"].location_id
    assert project.owner_id == stored_project["result"].owner_id


def test_get_projects_by_owner(db: Session) -> None:
    user = create_user(db)
    create_project(db, owner_id=user.id)
    create_project(db, owner_id=user.id)
    create_project(db, owner_id=user.id)
    projects = crud.project.get_user_project_list(db, user_id=user.id)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 3
    for project in projects:
        assert project.owner_id == user.id


def test_get_projects_by_project_member(db: Session) -> None:
    user = create_user(db)
    project = create_project(db)
    project2 = create_project(db)
    project3 = create_project(db)
    create_project_member(db, member_id=user.id, project_id=project.id)
    create_project_member(db, member_id=user.id, project_id=project2.id)
    create_project_member(db, member_id=user.id, project_id=project3.id)
    projects = crud.project.get_user_project_list(db, user_id=user.id)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 3
    for project in projects:
        assert project.id in [project.id, project2.id, project3.id]


def test_update_project(db: Session) -> None:
    project = create_project(db)
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


def test_get_project_flight_count(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    for _ in range(0, 5):
        create_flight(db, project_id=project.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert stored_project["result"].flight_count == 5


def test_get_project_flight_count_with_deactivated_flight(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    flight3 = create_flight(db, project_id=project.id)
    crud.flight.deactivate(db, flight_id=flight1.id)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert stored_project["result"].flight_count == 2


def test_deactivate_project(db: Session) -> None:
    project = create_project(db)
    project2 = crud.project.deactivate(db, project_id=project.id)
    project3 = crud.project.get(db, id=project.id)
    assert project2 and project3
    assert project3.id == project.id
    assert project3.is_active is False
    assert isinstance(project3.deactivated_at, datetime)
    assert project3.deactivated_at < datetime.utcnow()


def test_deactivate_project_deactivates_flights_and_data_products(db: Session) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)
    project2 = crud.project.deactivate(db, project_id=project.id)
    project3 = crud.project.get(db, id=project.id)
    assert project2 and project3
    assert project3.id == project.id
    assert project3.is_active is False
    flight2 = crud.flight.get(db, id=flight.id)
    assert flight2 and flight2.is_active is False
    data_product2 = crud.data_product.get(db, id=data_product.obj.id)
    assert data_product2 and data_product2.is_active is False


def test_get_deactivated_project_returns_none(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    crud.project.deactivate(db, project_id=project.id)
    project2 = crud.project.get_user_project(db, project_id=project.id, user_id=user.id)
    assert project2 and project2["result"] is None


def test_get_projects_ignores_deactivated_projects(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    project2 = create_project(db, owner_id=user.id)
    project3 = create_project(db, owner_id=user.id)
    crud.project.deactivate(db, project_id=project3.id)
    projects = crud.project.get_user_project_list(db, user_id=user.id)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 2
    for project in projects:
        assert project.id in [project.id, project2.id]
