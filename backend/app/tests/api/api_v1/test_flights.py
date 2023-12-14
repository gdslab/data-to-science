from random import randint

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.flight import SENSORS, PLATFORMS
from app.schemas.flight import FlightUpdate
from app.schemas.project_member import ProjectMemberCreate
from app.tests.utils.flight import create_flight, create_acquisition_date
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def test_create_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="owner")
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
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
    response_data = response.json()
    assert "id" in response_data
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="manager")
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="viewer")
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
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


def test_get_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="owner")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="manager")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="viewer")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="owner")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="manager")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="viewer")
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


def test_update_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="owner")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="manager")
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
    project_member_in = ProjectMemberCreate(member_id=current_user.id, role="viewer")
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
