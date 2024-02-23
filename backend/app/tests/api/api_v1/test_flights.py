from datetime import datetime
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
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight, create_acquisition_date
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_flight_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    pilot = create_user(db)
    project = create_project(db)
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role="owner", member_id=current_user.id, project_id=project.id
    )
    create_project_member(db, role="viewer", member_id=pilot.id, project_id=project.id)
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
    create_project_member(db, role="viewer", member_id=pilot.id, project_id=project.id)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
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
    create_project_member(db, role="viewer", member_id=pilot.id, project_id=project.id)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
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
    create_project_member(db, role="viewer", member_id=pilot.id, project_id=project.id)
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
        db, role="viewer", member_id=pilot.id, project_id=project.id
    )
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db, role="owner", member_id=current_user.id, project_id=project.id
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
        db, role="owner", member_id=current_user.id, project_id=project.id
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
            response_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
        )
    except Exception:
        raise
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.utcnow()


def test_deactivate_flight_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role="manager"
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
        db, member_id=current_user.id, project_id=project.id, role="viewer"
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
