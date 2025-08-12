from datetime import datetime, timezone

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas.project import ProjectUpdate
from app.schemas.team_member import TeamMemberUpdate, Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.project import (
    create_project,
    random_harvest_date,
    random_planting_date,
)
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user
from app.tests.utils.utils import (
    random_team_description,
    random_team_name,
    get_geojson_feature_collection,
)


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
        location=get_geojson_feature_collection("polygon")["geojson"]["features"][0],
        owner_id=user.id,
    )
    assert project.title == title
    assert project.description == description
    assert project.planting_date == planting_date
    assert project.harvest_date == harvest_date
    assert project.location_id
    assert project.owner_id == user.id
    assert project.is_active is True
    assert project.is_published is False


def test_create_project_with_team(db: Session) -> None:
    # Create team with owner, manager, and viewer
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    team_manager = create_user(db)
    team_viewer = create_user(db)
    create_team_member(db, email=team_manager.email, team_id=team.id, role=Role.MANAGER)
    create_team_member(db, email=team_viewer.email, team_id=team.id, role=Role.VIEWER)
    # Create project with team
    project = create_project(
        db,
        owner_id=team_owner.id,
        team_id=team.id,
    )
    assert project.owner_id == team_owner.id
    assert project.team_id == team.id
    # Get project members
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert len(project_members) == 3
    for project_member in project_members:
        if project_member.member_id == team_owner.id:
            assert project_member.role == Role.OWNER
        elif project_member.member_id == team_manager.id:
            assert project_member.role == Role.MANAGER
        elif project_member.member_id == team_viewer.id:
            assert project_member.role == Role.VIEWER


def test_create_project_with_team_not_owned_by_user(db: Session) -> None:
    user = create_user(db)
    other_user = create_user(db)
    team = create_team(db, owner_id=other_user.id)
    # Add user as team member with default "member" role
    create_team_member(db, email=user.email, team_id=team.id)
    # Create project with team not owned by user
    with pytest.raises(ValueError):
        create_project(
            db,
            owner_id=user.id,
            team_id=team.id,
        )


def test_create_project_creates_project_member_for_owner(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=user.id
    )
    assert project_member
    assert project_member.role == Role.OWNER
    assert user.id == project_member.member_id
    assert project.id == project_member.project_uuid


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
    assert project.is_active is True
    assert project.is_published is False


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
    assert project.is_active == stored_project["result"].is_active
    assert project.is_published == stored_project["result"].is_published


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
    assert project.is_active == stored_project["result"].is_active
    assert project.is_published == stored_project["result"].is_published


def test_get_projects_by_owner(db: Session) -> None:
    user = create_user(db)
    create_project(db, owner_id=user.id)
    create_project(db, owner_id=user.id)
    create_project(db, owner_id=user.id)
    projects = crud.project.get_user_projects(db, user=user)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 3
    for project in projects:
        assert project.owner_id == user.id


def test_get_projects_by_project_member(db: Session) -> None:
    user = create_user(db)
    project1 = create_project(db)
    project2 = create_project(db)
    project3 = create_project(db)
    create_project_member(db, member_id=user.id, project_uuid=project1.id)
    create_project_member(db, member_id=user.id, project_uuid=project2.id)
    create_project_member(db, member_id=user.id, project_uuid=project3.id)
    projects = crud.project.get_user_projects(db, user=user)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 3
    for project in projects:
        assert project.id in [project1.id, project2.id, project3.id]


def test_get_projects_with_data_products_by_type(db: Session) -> None:
    user = create_user(db)
    # create three projects
    project1 = create_project(db)
    project2 = create_project(db)
    project3 = create_project(db)
    projects = [project1, project2, project3]
    # add user as project member to all three projects
    create_project_member(db, member_id=user.id, project_uuid=project1.id)
    create_project_member(db, member_id=user.id, project_uuid=project2.id)
    create_project_member(db, member_id=user.id, project_uuid=project3.id)
    # create flight for each project
    for project_idx, project in enumerate(projects):
        flight = create_flight(db, project_id=project.id)
        # add raster data product to first project
        if project_idx == 0:
            SampleDataProduct(db, data_type="ortho", flight=flight, project=project)
        # add point cloud data product to second project
        if project_idx == 1:
            crud.data_product.create_with_flight(
                db,
                obj_in=schemas.DataProductCreate(
                    data_type="point_cloud",
                    filepath="null",
                    original_filename="test.las",
                ),
                flight_id=flight.id,
            )
    # get list of projects with raster data products
    projects_with_rasters = crud.project.get_user_projects(
        db, user=user, has_raster=True
    )
    assert projects_with_rasters
    assert isinstance(projects_with_rasters, list)
    assert len(projects_with_rasters) == 1
    assert projects_with_rasters[0].id == project1.id


def test_get_all_projects(db: Session) -> None:
    user = create_user(db, is_superuser=True)
    project1 = create_project(db, owner_id=user.id)
    project2 = create_project(db, owner_id=user.id)
    project3 = create_project(db)
    projects = crud.project.get_user_projects(db, user=user, include_all=True)
    assert len(projects) == 3
    for project in projects:
        assert project.id in [project1.id, project2.id, project3.id]


def test_update_project(db: Session) -> None:
    project = create_project(db)
    new_title = random_team_name()
    new_planting_date = random_planting_date()
    project_in_update = ProjectUpdate(title=new_title, planting_date=new_planting_date)
    project_update = crud.project.update_project(
        db,
        project_id=project.id,
        project_obj=project,
        project_in=project_in_update,
        user_id=project.owner_id,
    )

    assert project_update.get("response_code") == status.HTTP_200_OK
    assert project_update.get("message") == "Project updated successfully"
    updated_project = project_update.get("result")
    assert updated_project
    assert project.id == updated_project.id
    assert new_title == updated_project.title
    assert new_planting_date == updated_project.planting_date
    assert project.planting_date == updated_project.planting_date
    assert project.description == updated_project.description
    assert project.owner_id == updated_project.owner_id


def test_update_project_with_team(db: Session) -> None:
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Create team member and update role to owner
    team_member = create_team_member(db, team_id=team.id)
    updated_team_member = crud.team_member.update(
        db,
        db_obj=team_member,
        obj_in=TeamMemberUpdate(role=Role.OWNER),
    )
    assert updated_team_member.role == Role.OWNER

    # Add another team member with manager role
    team_member2 = create_team_member(db, team_id=team.id)
    updated_team_member2 = crud.team_member.update(
        db,
        db_obj=team_member2,
        obj_in=TeamMemberUpdate(role=Role.MANAGER),
    )
    assert updated_team_member2.role == Role.MANAGER

    # Add another team member with viewer role
    team_member3 = create_team_member(db, team_id=team.id)
    updated_team_member3 = crud.team_member.update(
        db,
        db_obj=team_member3,
        obj_in=TeamMemberUpdate(role=Role.VIEWER),
    )
    assert updated_team_member3.role == Role.VIEWER

    # Create project owned by team member and update it with the team
    project = create_project(db, owner_id=team_member.member_id)
    project_in_update = ProjectUpdate(team_id=team.id)
    project_update = crud.project.update_project(
        db,
        project_id=project.id,
        project_obj=project,
        project_in=project_in_update,
        user_id=project.owner_id,
    )
    assert project_update.get("response_code") == status.HTTP_200_OK
    assert project_update.get("message") == "Project updated successfully"
    updated_project = project_update.get("result")
    assert updated_project
    assert project.id == updated_project.id
    assert project.team_id == updated_project.team_id

    # Get project members
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert project_members
    # Team owner, team manager, team viewer, and project owner
    assert len(project_members) == 4
    # Team member and project member roles should match
    for project_member in project_members:
        if project_member.member_id == team_owner.id:
            assert project_member.role == Role.OWNER
        elif project_member.member_id == team_member2.member_id:
            assert project_member.role == Role.MANAGER
        elif project_member.member_id == team_member3.member_id:
            assert project_member.role == Role.VIEWER
        else:
            assert project_member.role == Role.OWNER


def test_update_project_with_team_not_owned_by_user(db: Session) -> None:
    team_owner = create_user(db)
    team = create_team(db, owner_id=team_owner.id)
    # Create team member with default "member" role
    team_member = create_team_member(db, team_id=team.id)

    # Create project owned by team member and update it with the team
    project = create_project(db, owner_id=team_member.member_id)
    project_in_update = ProjectUpdate(team_id=team.id)
    project_update = crud.project.update_project(
        db,
        project_id=project.id,
        project_obj=project,
        project_in=project_in_update,
        user_id=project.owner_id,
    )
    assert project_update.get("response_code") == status.HTTP_403_FORBIDDEN


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


def test_get_project_data_product_count(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, data_type="ortho", flight=flight, project=project)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert stored_project["result"].data_product_count == 1


def test_get_project_data_product_count_for_multiple_projects(db: Session) -> None:
    user = create_user(db)
    project1 = create_project(db, owner_id=user.id)
    project2 = create_project(db, owner_id=user.id)
    project3 = create_project(db, owner_id=user.id)
    flight1 = create_flight(db, project_id=project1.id)
    flight2 = create_flight(db, project_id=project2.id)
    flight3 = create_flight(db, project_id=project3.id)
    SampleDataProduct(db, data_type="ortho", flight=flight1, project=project1)
    SampleDataProduct(db, data_type="ortho", flight=flight2, project=project2)
    SampleDataProduct(db, data_type="ortho", flight=flight3, project=project3)
    stored_projects = crud.project.get_user_projects(db, user=user)
    assert len(stored_projects) == 3
    for project in stored_projects:
        if project.id == project1.id:
            assert project.data_product_count == 1
        elif project.id == project2.id:
            assert project.data_product_count == 1
        elif project.id == project3.id:
            assert project.data_product_count == 1


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


def test_get_most_recent_flight(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flights = []
    for _ in range(0, 5):
        flight = create_flight(db, project_id=project.id)
        flights.append(flight)
    stored_project = crud.project.get_user_project(
        db, project_id=project.id, user_id=user.id
    )
    assert stored_project and stored_project["result"]
    assert stored_project["result"].most_recent_flight
    most_recent_flight = None
    for flight in flights:
        if most_recent_flight:
            if most_recent_flight < flight.acquisition_date:
                most_recent_flight = flight.acquisition_date
        else:
            most_recent_flight = flight.acquisition_date
    assert stored_project["result"].most_recent_flight == most_recent_flight


def test_deactivate_project(db: Session) -> None:
    project = create_project(db)
    project2 = crud.project.deactivate(
        db, project_id=project.id, user_id=project.owner_id
    )
    project3 = crud.project.get(db, id=project.id)
    assert project2 and project3
    assert project3.id == project.id
    assert project3.is_active is False
    assert isinstance(project3.deactivated_at, datetime)
    assert project3.deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    )


def test_deactivate_project_deactivates_flights_and_data_products(db: Session) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)
    project2 = crud.project.deactivate(
        db, project_id=project.id, user_id=project.owner_id
    )
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
    crud.project.deactivate(db, project_id=project.id, user_id=user.id)
    project2 = crud.project.get_user_project(db, project_id=project.id, user_id=user.id)
    assert project2 and project2["result"] is None


def test_get_projects_ignores_deactivated_projects(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    project2 = create_project(db, owner_id=user.id)
    project3 = create_project(db, owner_id=user.id)
    crud.project.deactivate(db, project_id=project3.id, user_id=user.id)
    projects = crud.project.get_user_projects(db, user=user)
    assert projects
    assert isinstance(projects, list)
    assert len(projects) == 2
    for project_obj in projects:
        assert project_obj.id in [project.id, project2.id]
