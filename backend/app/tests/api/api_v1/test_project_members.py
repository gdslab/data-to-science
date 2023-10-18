from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


API_URL = f"{settings.API_V1_STR}/projects"


def test_get_project_members_by_owner(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
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


def test_add_new_project_member_by_email_and_project_owner(
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


def test_add_new_project_member_by_id_and_project_owner(
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


def test_add_new_project_member_by_email_and_regular_project_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(db, email=current_user.email, project_id=project.id)
    new_member = create_user(db)
    data = {"email": new_member.email}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    assert response.status_code == 403


def test_add_new_project_member_with_unused_email(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    data = {"email": "email@notindb.doh"}
    response = client.post(f"{API_URL}/{project.id}/members", json=data)
    assert 404 == response.status_code
