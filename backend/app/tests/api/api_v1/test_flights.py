import os
from datetime import datetime, timezone
from random import randint

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.flight import Flight, SENSORS, PLATFORMS
from app.schemas.data_product import DataProductCreate
from app.schemas.flight import FlightUpdate
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight, create_acquisition_date
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user


def test_create_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role=Role.OWNER, member_id=current_user.id, project_id=project.id
    )
    create_project_member(
        db, role=Role.VIEWER, member_id=pilot.id, project_id=project.id
    )
    data = {
        "name": "Test Flight",
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights", json=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert data["name"] == response_data["name"]
    assert data["acquisition_date"] == response_data["acquisition_date"]
    assert data["altitude"] == response_data["altitude"]
    assert data["side_overlap"] == response_data["side_overlap"]
    assert data["forward_overlap"] == response_data["forward_overlap"]
    assert data["sensor"] == response_data["sensor"]
    assert data["platform"] == response_data["platform"]


def test_create_flight_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role=Role.VIEWER, member_id=pilot.id, project_id=project.id
    )
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    data = {
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights", json=data
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_flight_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role=Role.VIEWER, member_id=pilot.id, project_id=project.id
    )
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    data = {
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_flight_with_non_project_member(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    create_project_member(
        db, role=Role.VIEWER, member_id=pilot.id, project_id=project.id
    )
    data = {
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/",
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_flight_with_pilot_that_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    pilot_project_member = create_project_member(
        db, role=Role.VIEWER, member_id=pilot.id, project_id=project.id
    )
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role=Role.OWNER, member_id=current_user.id, project_id=project.id
    )
    # remove pilot
    crud.project_member.remove(db, id=pilot_project_member.id)
    crud.user.remove(db, id=pilot.id)
    data = {
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_flight_with_pilot_that_does_not_belong_to_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role=Role.OWNER, member_id=current_user.id, project_id=project.id
    )
    data = {
        "acquisition_date": create_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights", json=data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.OWNER)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(flight.id)


def test_get_flight_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_flight_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.VIEWER)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_flight_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_flights_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.OWNER)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/flights")
    assert response.status_code == status.HTTP_200_OK
    flights = response.json()
    assert type(flights) is list
    assert len(flights) == 3
    for flight in flights:
        assert "project_id" in flight
        assert flight["project_id"] == str(project.id)


def test_get_flights_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/flights")
    assert response.status_code == status.HTTP_200_OK


def test_get_flights_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.VIEWER)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/flights")
    assert response.status_code == status.HTTP_200_OK


def test_get_flight_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_flights_with_raster_data(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    flight3 = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.VIEWER)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    # add raster data product to first flight
    raster_data_product = SampleDataProduct(
        db, data_type="ortho", flight=flight1, project=project
    )
    # add point cloud data product to second flight
    point_cloud_data_product = crud.data_product.create_with_flight(
        db,
        obj_in=DataProductCreate(
            data_type="point_cloud",
            filepath="null",
            original_filename="test.las",
        ),
        flight_id=flight2.id,
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights",
        params={"has_raster": True},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1
    assert response_data[0]["id"] == str(flight1.id)


def test_update_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.OWNER)
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
    )
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert str(flight.id) == response_data["id"]
    assert str(flight.project_id) == response_data["project_id"]
    assert flight_in.altitude == response_data["altitude"]


def test_update_flight_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
    )
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert response.status_code == status.HTTP_200_OK


def test_update_flight_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role=Role.VIEWER)
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
    )
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flight_with_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_flight_project_with_ownership_role_for_both_projects(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as owner (read/write/del)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    # add data product to flight
    data_product = SampleDataProduct(
        db, project=src_project, flight=flight, skip_job=True
    )
    # add raw data to flight
    raw_data = SampleRawData(db, project=src_project, flight=flight)
    # create destination project add current user as owner (read/write/del)
    dst_project = create_project(db, owner_id=current_user.id)
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(flight.id)
    assert response_data["project_id"] == str(dst_project.id)
    assert response_data["read_only"] is False
    # confirm data product moved to new static file location
    updated_data_product = crud.data_product.get(db, id=data_product.obj.id)
    assert updated_data_product
    new_data_product_location = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(dst_project.id),
        "flights",
        str(flight.id),
        "data_products",
        str(updated_data_product.id),
        os.path.basename(data_product.obj.filepath),
    )
    assert not os.path.exists(data_product.obj.filepath)  # old location
    assert os.path.exists(new_data_product_location)
    assert updated_data_product.filepath == new_data_product_location
    # confirm raw data moved to new static file location
    updated_raw_data = crud.raw_data.get(db, id=raw_data.obj.id)
    assert updated_raw_data
    new_raw_data_location = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(dst_project.id),
        "flights",
        str(flight.id),
        "raw_data",
        str(updated_raw_data.id),
        os.path.basename(raw_data.obj.filepath),
    )
    assert not os.path.exists(raw_data.obj.filepath)
    assert os.path.exists(new_raw_data_location)
    assert updated_raw_data.filepath == new_raw_data_location


def test_update_flight_project_with_manager_role_for_both_projects(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as manager (read/write)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=src_project.id,
    )
    # add data product to flight
    data_product = SampleDataProduct(
        db, project=src_project, flight=flight, skip_job=True
    )
    # create destination project add current user as manager (read/write)
    dst_project = create_project(db)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=dst_project.id,
    )
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flight_project_with_owner_role_for_src_project_and_manager_role_for_dst_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as owner (read/write/del)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    # create destination project add current user as manager (read/write)
    dst_project = create_project(db)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=dst_project.id,
    )
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flight_project_with_manager_role_for_src_project_and_owner_role_for_dst_project(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as manager (read/write)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=src_project.id,
    )
    # create destination project add current user as owner (read/write/del)
    dst_project = create_project(db, owner_id=current_user.id)
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flight_project_with_manager_role_for_both_src_and_dst_projects(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as manager (read/write)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=src_project.id,
    )
    # create destination project add current user as manager (read/write)
    dst_project = create_project(db)
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, role=Role.MANAGER
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=dst_project.id,
    )
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_flight_project_with_read_only_set_on_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create source project with a flight and add current user as manager (read/write)
    current_user = get_current_user(db, normal_user_access_token)
    src_project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, altitude=50, project_id=src_project.id)
    # add data product to flight
    data_product = SampleDataProduct(db, project=src_project, flight=flight)
    # create destination project add current user as manager (read/write)
    dst_project = create_project(db, owner_id=current_user.id)
    # set flight to "read_only"
    with db as session:
        statement = update(Flight).values(read_only=True).where(Flight.id == flight.id)
        session.execute(statement)
        session.commit()
    # request to move flight from source project to destination project
    response = client.put(
        f"{settings.API_V1_STR}/projects/{src_project.id}/flights/{flight.id}/move_to_project/{dst_project.id}",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_deactivate_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("is_active", True) is False
    try:
        deactivated_at = datetime.strptime(
            response_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except Exception:
        raise
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)


def test_deactivate_flight_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role=Role.MANAGER
    )
    flight = create_flight(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_flight_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role=Role.VIEWER
    )
    flight = create_flight(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_flight_by_non_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deactivate_flight_deactivates_data_products(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight)
    data_product2 = SampleDataProduct(db, project=project, flight=flight)
    data_product3 = SampleDataProduct(db, project=project, flight=flight)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("is_active", True) is False
    upload_dir = settings.TEST_STATIC_DIR
    data_products = [data_product1, data_product2, data_product3]
    for data_product in data_products:
        data_product = crud.data_product.get(db, id=data_product.obj.id)
        assert data_product.is_active is False
