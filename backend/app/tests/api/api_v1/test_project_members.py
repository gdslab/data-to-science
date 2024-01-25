import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.project_member import ProjectMemberUpdate
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


API_URL = f"{settings.API_V1_STR}/projects"


def test_create_project_member_by_email_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    new_member = create_user(db)
    data = {"email": new_member.email, "member_id": None}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    response.status_code == 201
    response_data = response.json()
    new_member.id == response_data["member_id"]
    project.id == response_data["project_id"]


def teset_create_project_member_by_user_id_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    new_member = create_user(db)
    data = {"member_id": str(new_member.id)}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    assert response.status_code == 201
    response_data = response.json()
    new_member.id == response_data["member_id"]
    project.id == response_data["project_id"]


def test_create_project_member_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    new_member = create_user(db)
    data = {"email": new_member.email}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_project_member_with_invalid_email(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    data = {"email": "email@notindb.doh"}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    assert 404 == response.status_code


def test_create_project_member_with_invalid_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db)
    with pytest.raises(DataError):
        create_project_member(
            db, email=current_user.email, project_id=project.id, role="invalid-role"
        )


def test_create_project_members_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db, owner_id=current_user.id)
    new_member1 = create_user(db)
    new_member2 = create_user(db)
    new_member3 = create_user(db)
    data = [new_member1.id, new_member2.id, new_member3.id]
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/members/multi",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert len(response_data) == 4  # three new members plus owner


def test_create_project_members_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role="manager"
    )
    new_member1 = create_user(db)
    new_member2 = create_user(db)
    new_member3 = create_user(db)
    data = [new_member1.id, new_member2.id, new_member3.id]
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/members/multi",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_members_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    project = create_project(db)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role="viewer"
    )
    new_member1 = create_user(db)
    new_member2 = create_user(db)
    new_member3 = create_user(db)
    data = [new_member1.id, new_member2.id, new_member3.id]
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/members/multi",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project_members_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    new_member1 = create_user(db)
    new_member2 = create_user(db)
    new_member3 = create_user(db)
    data = [new_member1.id, new_member2.id, new_member3.id]
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/members/multi",
        json=jsonable_encoder(data),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["member_id"] == str(current_user.id)
    assert response_data["project_id"] == str(project.id)
    assert response_data["role"] == "owner"


def test_get_project_member_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role="manager"
    )
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["member_id"] == str(current_user.id)
    assert response_data["project_id"] == str(project.id)
    assert response_data["role"] == "manager"


def test_get_project_member_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, member_id=current_user.id, project_id=project.id, role="viewer"
    )
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["member_id"] == str(current_user.id)
    assert response_data["project_id"] == str(project.id)
    assert response_data["role"] == "viewer"


def test_get_project_member_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    other_user = create_user(db)
    project = create_project(db, owner_id=other_user.id)
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_project_members(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    user2 = create_user(db)
    user3 = create_user(db)
    create_project_member(db, email=user2.email, project_id=project.id)
    create_project_member(db, email=user3.email, project_id=project.id)
    response = client.get(f"{API_URL}/{project.id}/members")
    assert response.status_code == 200
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 3
    for project_member in response_data:
        assert project_member["member_id"] in [
            str(current_user.id),
            str(user2.id),
            str(user3.id),
        ]


def test_get_project_members_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    for i in range(0, 3):
        create_project_member(db, project_id=project.id)
    response = client.get(f"{API_URL}/{project.id}/members")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    project_member = create_project_member(db, role="viewer")
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == 200
    updated_project_member = response.json()
    assert updated_project_member["id"] == str(project_member.id)
    assert updated_project_member["role"] == "manager"


def test_update_project_member_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="manager"
    )
    project_member = create_project_member(db, role="viewer")
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_member_with_project_viewer_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="viewer"
    )
    project_member = create_project_member(db, role="viewer")
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_member_without_process_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    project_member = create_project_member(db, member_id=project_owner.id)
    project_member_in = {"role": "owner"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    project_member = create_project_member(db, project_id=project.id, role="owner")
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_200_OK
    project_member_in_db = crud.project_member.get(db, id=project_member.id)
    assert project_member_in_db is None


def test_remove_project_member_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="manager"
    )
    project_member = create_project_member(db, project_id=project.id, role="owner")
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_project_member_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, email=current_user.email, project_id=project.id, role="viewer"
    )
    project_member = create_project_member(db, project_id=project.id, role="owner")
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_project_member_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    project_member = create_project_member(db, project_id=project.id)
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
