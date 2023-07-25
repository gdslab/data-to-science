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
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.flight import create_random_flight, create_random_acquisition_date
from app.tests.utils.user import create_random_user


def test_create_flight(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    """Verify new flight is created in database."""
    pilot = create_random_user(db)
    dataset = create_random_dataset(db, category="UAS")
    # add current user to project associated with dataset
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=dataset.project_id
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        member_id=current_user.id,
        project_id=dataset.project_id,
    )
    data = {
        "acquisition_date": create_random_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.post(
        f"{base_url}/flights/",
        headers=normal_user_token_headers,
        json=data,
    )
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
    normal_user_token_headers: dict[str, str],
) -> None:
    """Verify failure to create new flight when current user is not project member."""
    pilot = create_random_user(db)
    dataset = create_random_dataset(db, category="UAS")
    data = {
        "acquisition_date": create_random_acquisition_date(),
        "altitude": randint(0, 500),
        "side_overlap": randint(40, 80),
        "forward_overlap": randint(40, 80),
        "sensor": SENSORS[0],
        "platform": PLATFORMS[0],
        "pilot_id": pilot.id,
    }
    data = jsonable_encoder(data)
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.post(
        f"{base_url}/flights/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert 404 == r.status_code


def test_get_flight(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of flight the current user can access."""
    dataset = create_random_dataset(db, category="UAS")
    flight = create_random_flight(db, dataset_id=dataset.id)
    # add current user to project associated with dataset
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=dataset.project_id
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        member_id=current_user.id,
        project_id=dataset.project_id,
    )
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.get(
        f"{base_url}/flights/{flight.id}",
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    response_data = r.json()
    assert str(flight.id) == response_data["id"]


def test_get_flight_without_project_access(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to retrieve flight the current user cannot access."""
    dataset = create_random_dataset(db, category="UAS")
    flight = create_random_flight(db, dataset_id=dataset.id)
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.get(
        f"{base_url}/flights/{flight.id}",
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code


def test_update_flight(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update of flight in project current user can access."""
    dataset = create_random_dataset(db, category="UAS")
    flight = create_random_flight(db, altitude=50, dataset_id=dataset.id)
    # add current user to project associated with dataset
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    project_member_in = ProjectMemberCreate(
        member_id=current_user.id, project_id=dataset.project_id
    )
    crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        member_id=current_user.id,
        project_id=dataset.project_id,
    )
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.put(
        f"{base_url}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    response_data = r.json()
    assert str(flight.id) == response_data["id"]
    assert str(flight.dataset_id) == response_data["dataset_id"]
    assert flight_in.altitude == response_data["altitude"]


def test_update_flight_without_project_access(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to update flight in project current user cannot access."""
    dataset = create_random_dataset(db, category="UAS")
    flight = create_random_flight(db, altitude=50, dataset_id=dataset.id)
    flight_in = FlightUpdate(
        **{k: v for k, v in flight.__dict__.items() if k != "altitude"}, altitude=100
    )
    base_url = (
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}"
    )
    r = client.put(
        f"{base_url}/flights/{flight.id}",
        json=jsonable_encoder(flight_in),
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code
