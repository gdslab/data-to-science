from datetime import datetime, timezone
from typing import List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user import UserUpdate
from app.tests.utils.extension import (
    create_extension,
    create_team_extension,
    create_user_extension,
)
from app.tests.utils.team import create_team
from app.tests.utils.user import create_user, update_regular_user_to_superuser


def test_read_admin_users(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify admin can retrieve all users with admin fields."""
    # Create test users (approved and confirmed by default)
    user1 = create_user(db)
    user2 = create_user(db)
    # Create unapproved user
    user3 = create_user(db, is_approved=False)
    # Create unconfirmed user
    user4 = create_user(db, is_email_confirmed=False)

    # Update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)

    response = client.get(f"{settings.API_V1_STR}/admin/users")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, List)
    # Should include all 5 users (4 created + current superuser)
    assert len(users) == 5

    # Define expected admin fields
    expected_fields = {
        "id",
        "email",
        "first_name",
        "last_name",
        "created_at",
        "profile_url",
        "exts",
        "is_approved",
        "is_email_confirmed",
    }

    for user in users:
        # Verify ONLY expected admin fields are present (no extra fields)
        assert set(user.keys()) == expected_fields, (
            f"Unexpected fields in admin response. "
            f"Expected: {expected_fields}, Got: {set(user.keys())}"
        )
        # Verify is_superuser is NOT exposed
        assert "is_superuser" not in user


def test_read_admin_users_with_query(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify admin can search users with query parameter."""
    user1 = create_user(db, first_name="Alice", last_name="Admin")
    user2 = create_user(db, first_name="Bob", last_name="Builder")
    user3 = create_user(db, first_name="Charlie", last_name="Admin")

    # Update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    # Ensure superuser doesn't match query
    crud.user.update(
        db,
        db_obj=superuser,
        obj_in=UserUpdate(first_name="Superuser", last_name="Test"),
    )

    response = client.get(f"{settings.API_V1_STR}/admin/users?q=admin")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, List)
    assert len(users) == 2
    for user in users:
        assert user["last_name"] == "Admin"


def test_read_admin_users_non_superuser_forbidden(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify non-superuser cannot access admin users endpoint."""
    response = client.get(f"{settings.API_V1_STR}/admin/users")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_site_statistics_with_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/admin/site_statistics")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_project_statistics_with_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/admin/project_statistics")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_extensions(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create extensions
    extension1 = create_extension(db, name="ext1", description="Extension 1")
    extension2 = create_extension(db, name="ext2", description="Extension 2")
    extension3 = create_extension(db, name="ext3", description="Extension 3")
    # update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/admin/extensions")
    assert response.status_code == status.HTTP_200_OK
    extensions = response.json()
    assert isinstance(extensions, List)
    assert len(extensions) == 3
    for extension in extensions:
        assert extension["id"] in [
            str(extension1.id),
            str(extension2.id),
            str(extension3.id),
        ]


def test_get_extensions_by_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create extensions
    extension1 = create_extension(db, name="ext1", description="Extension 1")
    extension2 = create_extension(db, name="ext2", description="Extension 2")
    extension3 = create_extension(db, name="ext3", description="Extension 3")
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/admin/extensions")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_team_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    # update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    payload = {
        "team_id": str(team.id),
        "extension_id": str(extension.id),
        "is_active": True,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/team", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_200_OK
    team_extension = response.json()
    assert team_extension
    assert team_extension["extension_id"] == str(extension.id)
    assert team_extension["team_id"] == str(team.id)


def test_update_team_extension_with_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    payload = {
        "team_id": str(team.id),
        "extension_id": str(extension.id),
        "is_active": True,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/team", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_user_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    user = create_user(db)
    # update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    payload = {
        "user_id": str(user.id),
        "extension_id": str(extension.id),
        "is_active": True,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/user", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_200_OK
    user_extension = response.json()
    assert user_extension
    assert user_extension["extension_id"] == str(extension.id)
    assert user_extension["user_id"] == str(user.id)


def test_update_user_extension_with_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    user = create_user(db)
    payload = {
        "user_id": str(user.id),
        "extension_id": str(extension.id),
        "is_active": True,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/user", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_team_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    create_team_extension(db, extension_id=extension.id, team_id=team.id)
    # update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    payload = {
        "team_id": str(team.id),
        "extension_id": str(extension.id),
        "is_active": False,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/team", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_200_OK
    team_extension = response.json()
    assert team_extension
    assert team_extension["extension_id"] == str(extension.id)
    assert team_extension["team_id"] == str(team.id)
    deactivated_at = datetime.strptime(
        team_extension["deactivated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).replace(tzinfo=timezone.utc)
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.now(tz=timezone.utc)


def test_deactivate_user_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    user = create_user(db)
    create_user_extension(db, extension_id=extension.id, user_id=user.id)
    # update to superuser
    current_user = get_current_user(db, normal_user_access_token)
    superuser = update_regular_user_to_superuser(db, user_id=current_user.id)
    payload = {
        "user_id": str(user.id),
        "extension_id": str(extension.id),
        "is_active": False,
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/extensions/user", json=jsonable_encoder(payload)
    )
    assert response.status_code == status.HTTP_200_OK
    user_extension = response.json()
    assert user_extension
    assert user_extension["extension_id"] == str(extension.id)
    assert user_extension["user_id"] == str(user.id)
    deactivated_at = datetime.strptime(
        user_extension["deactivated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).replace(tzinfo=timezone.utc)
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.now(tz=timezone.utc)
