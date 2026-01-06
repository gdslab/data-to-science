from secrets import token_urlsafe
from typing import List

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserUpdate
from app.tests.utils.user import create_user, create_user_in
from app.tests.utils.utils import random_email, random_full_name, random_password


def test_create_user(db: Session) -> None:
    """Verify new user is created in database."""
    user_in = create_user_in()
    user = crud.user.create(db, obj_in=user_in)
    assert user.email == user_in.email
    assert hasattr(user, "hashed_password")
    assert not hasattr(user, "password")
    assert user.first_name == user_in.first_name
    assert user.last_name == user_in.last_name


def test_create_user_with_existing_email(db: Session) -> None:
    """Verify cannot create new user with an existing (non-unique) email."""
    user_in = create_user_in()
    user = crud.user.create(db, obj_in=user_in)
    with pytest.raises(IntegrityError):
        create_user(db, email=user.email)


def test_create_user_with_registration_intent(db: Session) -> None:
    """Verify user is created with registration_intent field."""
    registration_intent = "I want to use this platform for analyzing drone imagery from agricultural research projects."
    user_in = create_user_in(registration_intent=registration_intent)
    user = crud.user.create(db, obj_in=user_in)
    assert user.registration_intent == registration_intent


def test_create_user_without_registration_intent(db: Session) -> None:
    """Verify user is created without registration_intent (None)."""
    user_in = create_user_in()
    user = crud.user.create(db, obj_in=user_in)
    assert user.registration_intent is None


def test_get_user_by_id(db: Session) -> None:
    """Verify retrieving user by id returns correct user."""
    user = create_user(db)
    retrieved_user = crud.user.get_by_id(db, user_id=user.id)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert user.id == retrieved_user.id


def test_get_user_by_email(db: Session) -> None:
    """Verify retrieving user by email returns correct user."""
    user = create_user(db)
    retrieved_user = crud.user.get_by_email(db, email=user.email)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert user.id == retrieved_user.id


def test_get_user_by_api_key(db: Session) -> None:
    """Verify retrieving user by api key."""
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    retrieved_user = crud.user.get_by_api_key(db, api_key=api_key.api_key)
    assert retrieved_user
    assert retrieved_user.id == user.id


def test_get_user_by_invalid_api_key(db: Session) -> None:
    """Verify retrieving user by invalid api key fails."""
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    invalid_api_key1 = api_key.api_key[:-4]  # drop last four characters
    invalid_api_key2 = token_urlsafe()  # valid format, but not associated with user
    retrieved_user1 = crud.user.get_by_api_key(db, api_key=invalid_api_key1)
    retrieved_user2 = crud.user.get_by_api_key(db, api_key=invalid_api_key2)
    assert retrieved_user1 is None
    assert retrieved_user2 is None


def test_get_users(db: Session) -> None:
    """Verify retrieving multiple users."""
    user1 = create_user(db)
    user2 = create_user(db)
    user3 = create_user(db)
    # create user without approval
    create_user(db, is_approved=False)
    # create user and update email confirmation field to false
    user_without_confirmed_email = create_user(db)
    crud.user.update(
        db,
        db_obj=user_without_confirmed_email,
        obj_in=UserUpdate(is_email_confirmed=False),
    )
    users = crud.user.get_multi_by_query(db)
    assert users
    assert isinstance(users, List)
    assert len(users) == 3  # users without approval and email confirmation excluded
    for user in users:
        assert user.is_approved
        assert user.is_email_confirmed
        assert user.id in [user1.id, user2.id, user3.id]


def test_get_users_by_query(db: Session) -> None:
    """Verify retrieving multiple users by a query term."""
    user1 = create_user(db, first_name="Ellie", last_name="Sattler")
    user2 = create_user(db, first_name="Alan", last_name="Grant")
    user3 = create_user(db, first_name="Ian", last_name="Malcolm")
    users = crud.user.get_multi_by_query(db, q="Grant")
    assert users
    assert isinstance(users, List)
    assert len(users) == 1
    assert users[0].first_name == "Alan" and users[0].last_name == "Grant"


def test_update_user(db: Session) -> None:
    """Verify update changes user attributes in database."""
    user = create_user(db)
    new_password = random_password()
    new_first_name = random_full_name()["first"]
    user_in_update = UserUpdate(
        password=new_password,
        first_name=new_first_name,
    )
    updated_user = crud.user.update(db, db_obj=user, obj_in=user_in_update)
    assert updated_user
    assert user.email == updated_user.email
    assert user.first_name == new_first_name
    assert verify_password(new_password, updated_user.hashed_password)


def test_authenticate_user(db: Session) -> None:
    """Verify user is authenticated when correct credentials are provided."""
    user_in = create_user_in()
    user = crud.user.create(db, obj_in=user_in)
    authenticated_user = crud.user.authenticate(
        db, email=user_in.email, password=user_in.password
    )
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    """Verify user is not authentication when invalid credentials are provided."""
    email = random_email()
    password = random_password()
    user = crud.user.authenticate(db, email=email, password=password)
    assert user is None


def test_check_if_user_is_normal_user_by_default(db: Session) -> None:
    """Verify new user is not superuser by default at creation."""
    user = create_user(db)
    is_superuser = crud.user.is_superuser(user)
    assert is_superuser is False
