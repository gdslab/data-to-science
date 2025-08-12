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
from app.schemas.role import Role
from app.schemas.user import UserUpdate
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
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
    project.id == response_data["project_uuid"]


def test_create_project_member_by_user_id_with_project_owner_role(
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
    project.id == response_data["project_uuid"]


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
            db, email=current_user.email, project_uuid=project.id, role="invalid-role"  # type: ignore
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
        db, member_id=current_user.id, project_uuid=project.id, role=Role.MANAGER
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
        db, member_id=current_user.id, project_uuid=project.id, role=Role.VIEWER
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
    assert response_data["project_uuid"] == str(project.id)
    assert response_data["role"] == "owner"


def test_get_project_member_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    project_member = create_project_member(
        db, member_id=current_user.id, project_uuid=project.id
    )
    crud.project_member.update(
        db, db_obj=project_member, obj_in=ProjectMemberUpdate(role=Role.MANAGER)
    )
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["member_id"] == str(current_user.id)
    assert response_data["project_uuid"] == str(project.id)
    assert response_data["role"] == "manager"


def test_get_project_member_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db)
    create_project_member(
        db, member_id=current_user.id, project_uuid=project.id, role=Role.VIEWER
    )
    response = client.get(f"{API_URL}/{project.id}/members/{current_user.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["member_id"] == str(current_user.id)
    assert response_data["project_uuid"] == str(project.id)
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
    create_project_member(db, email=user2.email, project_uuid=project.id)
    create_project_member(db, email=user3.email, project_uuid=project.id)
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
        create_project_member(db, project_uuid=project.id)
    response = client.get(f"{API_URL}/{project.id}/members")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    # Create project member with viewer role
    project_member = create_project_member(db, role=Role.VIEWER)
    # Update project member role to manager
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_200_OK
    updated_project_member = response.json()
    assert updated_project_member["id"] == str(project_member.id)
    assert updated_project_member["role"] == "manager"


def test_update_project_member_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project not owned by current user
    project = create_project(db)
    # Add current user as manager to project
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    create_project_member(
        db, email=current_user.email, project_uuid=project.id, role=Role.MANAGER
    )
    # Create project member with viewer role
    project_member = create_project_member(db, role=Role.VIEWER)
    # Update project member role to manager
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_member_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project not owned by current user
    project = create_project(db)
    # Add current user as viewer to project
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    create_project_member(
        db, email=current_user.email, project_uuid=project.id, role=Role.VIEWER
    )
    # Create project member with viewer role
    project_member = create_project_member(db, role=Role.VIEWER)
    # Update project member role to manager
    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_member_without_process_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project not owned by current user
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    # Create project member with viewer role
    project_member = create_project_member(db, member_id=project_owner.id)
    # Update project member role to owner
    project_member_in = {"role": "owner"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_demo_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project owned by current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    # Create project member with viewer role
    project_member = create_project_member(db, role=Role.VIEWER)
    # Get demo user instance
    demo_user = crud.user.get(db, id=project_member.member_id)
    assert demo_user is not None
    # Update project member to demo user
    crud.user.update(db, db_obj=demo_user, obj_in=UserUpdate(is_demo=True))

    project_member_in = {"role": "manager"}
    response = client.put(
        f"{API_URL}/{project.id}/members/{project_member.id}", json=project_member_in
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_project_member_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    project_member = create_project_member(db, project_uuid=project.id, role=Role.OWNER)
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
        db, email=current_user.email, project_uuid=project.id, role=Role.MANAGER
    )
    project_member = create_project_member(db, project_uuid=project.id, role=Role.OWNER)
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
        db, email=current_user.email, project_uuid=project.id, role=Role.VIEWER
    )
    project_member = create_project_member(db, project_uuid=project.id, role=Role.OWNER)
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_project_member_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    project_member = create_project_member(db, project_uuid=project.id)
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_project_member_that_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    project_member = create_project_member(db, project_uuid=project.id, role=Role.OWNER)
    crud.project_member.remove(db, id=project_member.id)
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_project_owner_as_project_member_fails(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create project with current user as owner
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )
    project = create_project(db, owner_id=current_user.id)
    # get project member instance for current user/project owner
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=current_user.id
    )
    assert project_member is not None
    # attempt to remove current user from project member table
    response = client.delete(f"{API_URL}/{project.id}/members/{project_member.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
