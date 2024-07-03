from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.iforester import IForesterCreate, IForesterUpdate
from app.tests.crud.test_iforester_crud import EXAMPLE_DATA
from app.tests.utils.iforester import create_iforester
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["dbh"] == EXAMPLE_DATA.get("dbh")
    assert response_data["depthFile"] == EXAMPLE_DATA.get("depthFile")
    assert response_data["distance"] == EXAMPLE_DATA.get("distance")
    assert response_data["imageFile"] == EXAMPLE_DATA.get("imageFile")
    assert response_data["latitude"] == EXAMPLE_DATA.get("latitude")
    assert response_data["longitude"] == EXAMPLE_DATA.get("longitude")
    assert response_data["note"] == EXAMPLE_DATA.get("note")
    assert response_data["phoneDirection"] == EXAMPLE_DATA.get("phoneDirection")
    assert response_data["phoneID"] == EXAMPLE_DATA.get("phoneID")
    assert response_data["species"] == EXAMPLE_DATA.get("species")
    assert response_data["user"] == EXAMPLE_DATA.get("user")


def test_create_iforester_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    payload = EXAMPLE_DATA
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data


def test_create_iforester_record_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    payload = EXAMPLE_DATA
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester", json=payload
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_iforester_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    payload = EXAMPLE_DATA
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester", json=payload
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data
    assert response_data["dbh"] == EXAMPLE_DATA.get("dbh")
    assert response_data["depthFile"] == EXAMPLE_DATA.get("depthFile")
    assert response_data["distance"] == EXAMPLE_DATA.get("distance")
    assert response_data["imageFile"] == EXAMPLE_DATA.get("imageFile")
    assert response_data["latitude"] == EXAMPLE_DATA.get("latitude")
    assert response_data["longitude"] == EXAMPLE_DATA.get("longitude")
    assert response_data["note"] == EXAMPLE_DATA.get("note")
    assert response_data["phoneDirection"] == EXAMPLE_DATA.get("phoneDirection")
    assert response_data["phoneID"] == EXAMPLE_DATA.get("phoneID")
    assert response_data["species"] == EXAMPLE_DATA.get("species")
    assert response_data["user"] == EXAMPLE_DATA.get("user")


def test_read_iforester_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data


def test_read_iforester_record_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data


def test_read_iforester_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    old_species = iforester.species
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data
    assert old_species != new_species
    assert response_data["species"] == new_species


def test_update_iforester_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    old_species = iforester.species
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data


def test_update_iforester_record_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    old_species = iforester.species
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_iforester_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    iforester = create_iforester(db, project_id=project.id)
    old_species = iforester.species
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data
    assert response_data["id"] == str(iforester.id)


def test_remove_iforester_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_iforester_record_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    iforester = create_iforester(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_iforester_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
