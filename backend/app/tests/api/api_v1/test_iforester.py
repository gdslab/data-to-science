import os
from typing import List

import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.enums.api_key_scope import APIKeyScope
from app.schemas.iforester import IForesterUpdate
from app.schemas.role import Role
from app.tests.conftest import pytest_requires_iforester
from app.tests.utils.iforester import (
    EXAMPLE_DATA,
    EXAMPLE_IMAGE,
    EXAMPLE_PNG,
    create_iforester,
)
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def scope_error(scope: APIKeyScope) -> str:
    return f"API key does not have the '{scope.value}' scope"


@pytest_requires_iforester
def test_create_iforester_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    payload = {**EXAMPLE_DATA, "image": EXAMPLE_IMAGE, "png": EXAMPLE_PNG}
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


@pytest_requires_iforester
def test_create_iforester_record_with_project_owner_role_and_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    payload = {**EXAMPLE_DATA, "image": EXAMPLE_IMAGE, "png": EXAMPLE_PNG}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        json=payload,
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data


@pytest_requires_iforester
def test_create_iforester_record_with_create_only_api_key(
    client: TestClient, db: Session
) -> None:
    # a key embedded in a mobile app can add records but cannot read project data
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.CREATE]
    ).api_key
    project = create_project(db, owner_id=user.id)
    payload = {**EXAMPLE_DATA, "image": EXAMPLE_IMAGE, "png": EXAMPLE_PNG}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        json=payload,
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(crud.iforester.get_multi_iforester_by_project_id(db, project.id)) == 1
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(APIKeyScope.READ)


@pytest_requires_iforester
@pytest.mark.parametrize(
    "scopes", [[APIKeyScope.READ], [APIKeyScope.UPDATE], [APIKeyScope.DELETE]]
)
def test_create_iforester_requires_create_scope(
    client: TestClient, db: Session, scopes: List[APIKeyScope]
) -> None:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id, scopes=scopes).api_key
    project = create_project(db, owner_id=user.id)
    payload = {**EXAMPLE_DATA, "image": EXAMPLE_IMAGE, "png": EXAMPLE_PNG}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        json=payload,
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(APIKeyScope.CREATE)
    assert crud.iforester.get_multi_iforester_by_project_id(db, project.id) == []


@pytest_requires_iforester
def test_read_iforester_rejects_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    # key has every scope and its owner owns the project; the auth method is rejected
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_iforester
def test_read_multi_iforester_rejects_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_iforester
def test_read_multi_iforester_rejects_create_only_api_key(
    client: TestClient, db: Session
) -> None:
    # a leaked mobile app key cannot be used to read the records it created
    user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=user.id, scopes=[APIKeyScope.CREATE]
    ).api_key
    project = create_project(db, owner_id=user.id)
    create_iforester(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_iforester
def test_update_iforester_rejects_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    original_species = iforester.species
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(IForesterUpdate(species="Oak")),
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    iforester_in_db = crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester.id, project_id=project.id
    )
    assert iforester_in_db
    assert iforester_in_db.species == original_species


@pytest_requires_iforester
def test_delete_iforester_rejects_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    iforester = create_iforester(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester.id, project_id=project.id
    )


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
def test_read_multi_iforester_records_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_iforester(db, project_id=project.id)
    create_iforester(db, project_id=project.id)
    create_iforester(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/iforester")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_iforester
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


@pytest_requires_iforester
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
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data


@pytest_requires_iforester
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
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_iforester
def test_update_iforester_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    iforester = create_iforester(db, project_id=project.id)
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/iforester/{iforester.id}",
        json=jsonable_encoder(iforester_update_in),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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


@pytest_requires_iforester
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
