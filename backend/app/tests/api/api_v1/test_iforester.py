import os
from typing import List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_approved_user_by_jwt_or_api_key,
)
from app.core.config import settings
from app.schemas.iforester import IForesterUpdate
from app.schemas.role import Role
from app.tests.utils.iforester import (
    create_iforester,
    EXAMPLE_DATA,
    EXAMPLE_IMAGE,
    EXAMPLE_PNG,
)
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA
    payload["image"] = EXAMPLE_IMAGE
    payload["png"] = EXAMPLE_PNG
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["dbh"] == EXAMPLE_DATA.get("DBH")
    assert os.path.exists(response_data["depthFile"])
    assert response_data["distance"] == EXAMPLE_DATA.get("distance")
    assert os.path.exists(response_data["imageFile"])
    assert response_data["latitude"] == EXAMPLE_DATA.get("latitude")
    assert response_data["longitude"] == EXAMPLE_DATA.get("longitude")
    assert response_data["note"] == EXAMPLE_DATA.get("note")
    assert response_data["phoneDirection"] == EXAMPLE_DATA.get("phoneDirection")
    assert response_data["phoneID"] == EXAMPLE_DATA.get("phoneID")
    assert response_data["species"] == EXAMPLE_DATA.get("species")
    assert response_data["user"] == EXAMPLE_DATA.get("user")


def test_create_iforester_record_with_project_owner_role_and_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, api_key=normal_user_api_key
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA
    payload["image"] = EXAMPLE_IMAGE
    payload["png"] = EXAMPLE_PNG
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        json=payload,
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data


def test_create_iforester_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
    assert response_data["dbh"] == EXAMPLE_DATA.get("DBH")
    assert os.path.exists(response_data["depthFile"])
    assert response_data["distance"] == EXAMPLE_DATA.get("distance")
    assert os.path.exists(response_data["imageFile"])
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
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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


def test_read_multi_iforester_records_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    iforester1 = create_iforester(db, project_id=project.id)
    iforester2 = create_iforester(db, project_id=project.id)
    iforester3 = create_iforester(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/iforester")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, List)
    assert len(response_data) == 3
    for iforester in response_data:
        assert iforester["id"] in [
            str(iforester1.id),
            str(iforester2.id),
            str(iforester3.id),
        ]


def test_read_multi_iforester_records_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    iforester1 = create_iforester(db, project_id=project.id)
    iforester2 = create_iforester(db, project_id=project.id)
    iforester3 = create_iforester(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/iforester")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, List)
    assert len(response_data) == 3
    for iforester in response_data:
        assert iforester["id"] in [
            str(iforester1.id),
            str(iforester2.id),
            str(iforester3.id),
        ]


def test_read_multi_iforester_records_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    iforester1 = create_iforester(db, project_id=project.id)
    iforester2 = create_iforester(db, project_id=project.id)
    iforester3 = create_iforester(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/iforester")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, List)
    assert len(response_data) == 3
    for iforester in response_data:
        assert iforester["id"] in [
            str(iforester1.id),
            str(iforester2.id),
            str(iforester3.id),
        ]


def test_read_multi_iforester_records_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    iforester1 = create_iforester(db, project_id=project.id)
    iforester2 = create_iforester(db, project_id=project.id)
    iforester3 = create_iforester(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/iforester")
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
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
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
