import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserUpdate
from app.tests.utils.user import create_random_user, create_random_user_in
from app.tests.utils.utils import random_email, random_full_name, random_password


def test_create_user(db: Session) -> None:
    """Verify new user is created in database."""
    user_in = create_random_user_in()
    user = crud.user.create(db, obj_in=user_in)
    assert user.email == user_in.email
    assert hasattr(user, "hashed_password")
    assert not hasattr(user, "password")
    assert user.first_name == user_in.first_name
    assert user.last_name == user_in.last_name


def test_create_user_with_existing_email(db: Session) -> None:
    """Verify cannot create new user with an existing (non-unique) email."""
    user_in = create_random_user_in()
    user = crud.user.create(db, obj_in=user_in)
    with pytest.raises(IntegrityError):
        create_random_user(db, email=user.email)


def test_get_user_by_id(db: Session) -> None:
    """Verify retrieving user by id returns correct user."""
    user = create_random_user(db)
    retrieved_user = crud.user.get(db, id=user.id)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert jsonable_encoder(user) == jsonable_encoder(retrieved_user)


def test_get_user_by_email(db: Session) -> None:
    """Verify retrieving user by email returns correct user."""
    user = create_random_user(db)
    retrieved_user = crud.user.get_by_email(db, email=user.email)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert jsonable_encoder(user) == jsonable_encoder(retrieved_user)


def test_update_user(db: Session) -> None:
    """Verify update changes user attributes in database."""
    user = create_random_user(db)
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
    user_in = create_random_user_in()
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
    user = create_random_user(db)
    is_superuser = crud.user.is_superuser(user)
    assert is_superuser is False
