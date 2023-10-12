from random import randint

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


def test_create_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify new flight is created in database."""
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
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
    r = client.post(f"{settings.API_V1_STR}/projects/{project.id}/flights/", json=data)
    assert 201 == r.status_code
    response_data = r.json()
    assert "id" in response_data
    assert data["acquisition_date"] == response_data["acquisition_date"]
    assert data["altitude"] == response_data["altitude"]
    assert data["side_overlap"] == response_data["side_overlap"]
    assert data["forward_overlap"] == response_data["forward_overlap"]
    assert data["sensor"] == response_data["sensor"]
    assert data["platform"] == response_data["platform"]


def test_create_flight_without_project_access(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Verify failure to create new flight when current user is not project member."""
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
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/",
        json=data,
    )
    assert 404 == r.status_code


def test_get_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of flight the current user can access."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert 200 == r.status_code
    response_data = r.json()
    assert str(flight.id) == response_data["id"]


def test_get_flights(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of flights associated with project."""
    project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project.id
    )
    r = client.get(f"{settings.API_V1_STR}/projects/{project.id}/flights")
    assert 200 == r.status_code
    flights = r.json()
    assert type(flights) is list
    assert len(flights) == 3
    for flight in flights:
        assert "project_id" in flight
        assert flight["project_id"] == str(project.id)


def test_get_flight_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to retrieve flight the current user cannot access."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
    )
    assert 404 == r.status_code


def test_update_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify update of flight in project current user can access."""
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    current_user = get_current_user(db, normal_user_access_token)
    project_member_in = ProjectMemberCreate(member_id=current_user.id)
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_id=project.id,
    )
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert 200 == r.status_code
    response_data = r.json()
    assert str(flight.id) == response_data["id"]
    assert str(flight.project_id) == response_data["project_id"]
    assert flight_in.altitude == response_data["altitude"]


def test_update_flight_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify failure to update flight in project current user cannot access."""
    project = create_project(db)
    flight = create_flight(db, altitude=50, project_id=project.id)
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
    )
    assert 404 == r.status_code
