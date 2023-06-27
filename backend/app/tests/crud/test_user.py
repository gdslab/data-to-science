from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.user import create_random_user, create_random_user_in
from app.tests.utils.utils import random_email, random_full_name, random_password


def test_create_user(db: Session) -> None:
    """Test that correct attribute values are stored in database for newly created user."""
    user_in = create_random_user_in()
    user = crud.user.create(db=db, obj_in=user_in)
    assert user.email == user_in.email
    assert hasattr(user, "hashed_password")
    assert not hasattr(user, "password")
    assert user.first_name == user_in.first_name
    assert user.last_name == user_in.last_name


def test_authenticate_user(db: Session) -> None:
    """Test that user is authenticated when proper credentials provided."""
    user_in = create_random_user_in()
    user = crud.user.create(db=db, obj_in=user_in)
    authenticated_user = crud.user.authenticate(db, email=user_in.email, password=user_in.password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    """Test that user is not aunthenticated when invalid email and/or password provided."""
    email = random_email()
    password = random_password()
    user = crud.user.authenticate(db, email=email, password=password)
    assert user is None


def test_check_if_user_is_not_approved_by_default(db: Session) -> None:
    """Test that newly created user is not approved."""
    user = create_random_user(db)
    assert crud.user.is_approved(user) is False


def test_check_if_user_is_normal_user_by_default(db: Session) -> None:
    """Test that newly created user is not superuser."""
    user = create_random_user(db)
    is_superuser = crud.user.is_superuser(user)
    assert is_superuser is False


def test_get_user_by_id(db: Session) -> None:
    """Test that fetching user by id returns correct user."""
    user = create_random_user(db)
    retrieved_user = crud.user.get(db, id=user.id)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert jsonable_encoder(user) == jsonable_encoder(retrieved_user)


def test_get_user_by_email(db: Session) -> None:
    """Test that fetching user by email returns correct user."""
    user = create_random_user(db)
    retrieved_user = crud.user.get_by_email(db, email=user.email)
    assert retrieved_user
    assert user.email == retrieved_user.email
    assert jsonable_encoder(user) == jsonable_encoder(retrieved_user)


def test_update_user(db: Session) -> None:
    """Test that user attribute values update."""
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
