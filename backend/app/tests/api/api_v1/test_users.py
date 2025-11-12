import os
from typing import List

from fastapi import Request, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.mail import fm
from app.crud.crud_user import find_profile_img
from app.schemas.user import UserUpdate
from app.tests.utils.extension import (
    create_extension,
    create_team_extension,
    create_user_extension,
)
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user
from app.tests.conftest import pytest_requires_mail
from app.tests.utils.utils import random_email, random_full_name, random_password


@pytest_requires_mail
def test_create_user_new_email(client: TestClient, db: Session) -> None:
    """Verify new user is created in database."""
    api_domain = settings.API_DOMAIN
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": random_password(),
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    # skip test if email is disabled
    if fm:
        fm.config.SUPPRESS_SEND = 1
        with fm.record_messages() as outbox:
            r = client.post(f"{settings.API_V1_STR}/users/", json=data)
        assert 201 == r.status_code
        created_user = r.json()
        user = crud.user.get_by_email(db, email=data["email"])
        assert user
        assert user.email == created_user["email"]
        assert len(outbox) == 2
        assert (
            outbox[0]["from"]
            == settings.MAIL_FROM_NAME + " <" + settings.MAIL_FROM + ">"
        )
        assert outbox[0]["To"] == user.email
        assert outbox[0]["Subject"] == "Welcome to Data to Science - please confirm your email"
        assert (
            outbox[1]["from"]
            == settings.MAIL_FROM_NAME + " <" + settings.MAIL_FROM + ">"
        )
        assert outbox[1]["To"] == settings.MAIL_ADMINS.replace(",", ", ")
        assert outbox[1]["Subject"] == f"New Data to Science account awaiting approval ({api_domain})"


def test_create_user_existing_email(client: TestClient, db: Session) -> None:
    """Verify new user is not created in database when existing email provided."""
    existing_user = create_user(db, email=random_email())
    data = {
        "email": existing_user.email,
        "password": random_password(),
        "first_name": existing_user.first_name,
        "last_name": existing_user.last_name,
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert 409 == r.status_code


def test_create_user_is_not_approved(client: TestClient, db: Session) -> None:
    """Verify new user is not approved by default when email is enabled."""
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": random_password(),
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert 201 == r.status_code
    created_user = r.json()
    if settings.MAIL_ENABLED:
        assert created_user["is_approved"] is False
    else:
        assert created_user["is_approved"]


def test_create_user_with_password_less_than_minimum_length(
    client: TestClient, db: Session
) -> None:
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": "shortpass",
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    response = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_with_password_with_more_than_two_repeating_chars_in_a_row(
    client: TestClient, db: Session
) -> None:
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": "invalidpasssword",
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    response = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_users_normal_current_user(
    client: TestClient,
    normal_user_access_token: str,
) -> None:
    """Verify normal user can be retrieved with JWT token."""
    response = client.get(f"{settings.API_V1_STR}/users/current")
    assert response.status_code == status.HTTP_200_OK
    current_user = response.json()
    assert current_user
    assert settings.EMAIL_TEST_USER == current_user["email"]


def test_read_users_without_query(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of users without a query parameter."""
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/users")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, List)
    assert len(users) == 4  # three users created here plus user making request
    for user in users:
        assert user["is_approved"]
        assert user["is_email_confirmed"]
        assert user["id"] in [
            str(user1.id),
            str(user2.id),
            str(user3.id),
            str(current_user.id),
        ]


def test_read_users_with_query(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of users with a query parameter."""
    user1 = create_user(db, first_name="Bill", last_name="Harding")
    user2 = create_user(db, first_name="Jo", last_name="Harding")
    user3 = create_user(db, first_name="Dustin", last_name="Davis")
    # ensure current user not randomly assigned name that matches query term
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(
        db, db_obj=current_user, obj_in=UserUpdate(first_name="Dorothy", last_name="IV")
    )
    response = client.get(f"{settings.API_V1_STR}/users?q=harding")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, List)
    assert len(users) == 2
    assert users[0]["last_name"] == "Harding" and users[1]["last_name"] == "Harding"


def test_update_user(
    request: Request,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Verify update changes user attributes in database."""
    current_user = get_current_user(db, normal_user_access_token)
    full_name = random_full_name()
    user_in = UserUpdate(
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    response = client.put(
        f"{settings.API_V1_STR}/users/{current_user.id}",
        json=user_in.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user
    assert str(current_user.id) == updated_user["id"]
    assert full_name["first"] == updated_user["first_name"]
    assert full_name["last"] == updated_user["last_name"]


def test_update_demo_user(
    request: Request,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Verify update changes user attributes in database."""
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    full_name = random_full_name()
    user_in = UserUpdate(
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    response = client.put(
        f"{settings.API_V1_STR}/users/{current_user.id}",
        json=user_in.model_dump(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_profile(
    request: Request, client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    profile_img_path = os.path.join(
        os.sep, "app", "app", "tests", "data", "profile.png"
    )
    with open(profile_img_path, "rb") as profile_img_file:
        response = client.post(
            f"{settings.API_V1_STR}/users/profile", files={"files": profile_img_file}
        )
        assert response.status_code == status.HTTP_200_OK
        profile_img_filename = find_profile_img(str(current_user.id))
        assert profile_img_filename
        profile_img_static_filepath = os.path.join(
            settings.TEST_STATIC_DIR,
            f"users/{current_user.id}/{profile_img_filename}",
        )
        assert os.path.exists(profile_img_static_filepath)


def test_update_demo_user_profile(
    request: Request, client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    profile_img_path = os.path.join(
        os.sep, "app", "app", "tests", "data", "profile.png"
    )
    with open(profile_img_path, "rb") as profile_img_file:
        response = client.post(
            f"{settings.API_V1_STR}/users/profile", files={"files": profile_img_file}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_user_extensions(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db)
    create_team_member(db, email=current_user.email, team_id=team.id)
    extension1 = create_extension(db, name="ext1")
    extension2 = create_extension(db, name="ext2")
    create_user_extension(db, extension_id=extension1.id, user_id=current_user.id)
    create_team_extension(db, extension_id=extension2.id, team_id=team.id)
    response = client.get(f"{settings.API_V1_STR}/users/extensions")
    assert response.status_code == status.HTTP_200_OK
    extensions = response.json()
    assert isinstance(extensions, List)
    assert len(extensions) == 2
    assert "ext1" in extensions and "ext2" in extensions


def test_read_user_extensions_for_user_with_both_user_and_team_image_processing_extensions_returns_only_user_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db)
    create_team_member(db, email=current_user.email, team_id=team.id)
    extension1 = create_extension(db, name="odm")
    extension2 = create_extension(db, name="metashape")
    create_user_extension(db, extension_id=extension1.id, user_id=current_user.id)
    create_team_extension(db, extension_id=extension2.id, team_id=team.id)
    response = client.get(f"{settings.API_V1_STR}/users/extensions")
    assert response.status_code == status.HTTP_200_OK
    extensions = response.json()
    assert isinstance(extensions, List)
    assert len(extensions) == 1
    assert "odm" in extensions


def test_read_user_extensions_for_user_with_odm_and_metashape_user_extensions_returns_only_metashape_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    extension1 = create_extension(db, name="odm")
    extension2 = create_extension(db, name="metashape")
    create_user_extension(db, extension_id=extension1.id, user_id=current_user.id)
    create_user_extension(db, extension_id=extension2.id, user_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/users/extensions")
    assert response.status_code == status.HTTP_200_OK
    extensions = response.json()
    assert isinstance(extensions, List)
    assert len(extensions) == 1
    assert "metashape" in extensions


def test_read_user_extensions_for_user_with_odm_and_metashape_team_extensions_returns_only_metashape_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    team = create_team(db)
    create_team_member(db, email=current_user.email, team_id=team.id)
    extension1 = create_extension(db, name="odm")
    extension2 = create_extension(db, name="metashape")
    create_team_extension(db, extension_id=extension1.id, team_id=team.id)
    create_team_extension(db, extension_id=extension2.id, team_id=team.id)
    response = client.get(f"{settings.API_V1_STR}/users/extensions")
    assert response.status_code == status.HTTP_200_OK
    extensions = response.json()
    assert isinstance(extensions, List)
    assert len(extensions) == 1
    assert "metashape" in extensions
