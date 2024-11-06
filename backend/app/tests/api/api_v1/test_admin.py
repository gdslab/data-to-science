import datetime
from typing import List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.extension import (
    create_extension,
    create_team_extension,
    create_user_extension,
)
from app.tests.utils.team import create_team
from app.tests.utils.user import create_user, update_regular_user_to_superuser


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
    deactivated_at = datetime.datetime.strptime(
        team_extension.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
    ).replace(tzinfo=datetime.timezone.utc)
    assert isinstance(deactivated_at, datetime.datetime)
    assert deactivated_at < datetime.datetime.now(datetime.UTC)


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
    deactivated_at = datetime.datetime.strptime(
        user_extension.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
    ).replace(tzinfo=datetime.timezone.utc)
    assert isinstance(deactivated_at, datetime.datetime)
    assert deactivated_at < datetime.datetime.now(datetime.UTC)
