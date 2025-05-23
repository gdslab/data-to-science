from fastapi.testclient import TestClient
from pydantic import UUID4
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.single_use_token import SingleUseTokenCreate
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_full_name, random_password


def login_and_get_access_token(*, client: TestClient, email: str, password: str) -> str:
    """Generate authorization header for provided user credentials."""
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/auth/access-token", data=data)
    auth_token = r.cookies.get("access_token")
    if auth_token:
        return auth_token.split(" ")[1].rstrip('"')
    else:
        raise Exception("Unable to find access token")


def login_and_get_api_key(*, client: TestClient, email: str, password: str) -> str:
    """Generate authorization header for provided user credentials."""
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/auth/access-token", data=data)
    api_key = r.headers.get("X-API-KEY")
    if api_key:
        return api_key
    else:
        raise Exception("Unable to find access token")


def create_user_in(
    email: str | None = None,
    password: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> UserCreate:
    """Create random user model with specific email if provided."""
    if not email:
        email = random_email()
    if not password:
        password = random_password()
    if first_name and last_name:
        full_name = {"first": first_name, "last": last_name}
    else:
        full_name = random_full_name()
    user_in = UserCreate(
        email=email,
        password=password,
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    return user_in


def update_regular_user_to_superuser(db: Session, user_id: UUID4) -> User:
    """Updates a regular user to superuser role.

    Args:
        db (Session): Database session.
        user_id (UUID4): User's ID.

    Raises:
        ValueError: Raised if no user found for ID.

    Returns:
        User: Updated user.
    """
    user = crud.user.get(db, id=user_id)
    if user:
        statement = update(User).where(User.id == user.id).values(is_superuser=True)
        with db as session:
            session.execute(statement)
            session.commit()
    else:
        raise ValueError(f"User does not exist with this id: {user_id}")

    return crud.user.get(db, id=user_id)


def create_user(
    db: Session,
    email: str | None = None,
    password: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    is_approved: bool = True,
    is_superuser: bool = False,
    token: str | None = None,
    token_expired: bool = False,
) -> User:
    """Create random user in database with specific email if provided."""
    user_in = create_user_in(
        email=email, password=password, first_name=first_name, last_name=last_name
    )
    user = crud.user.create(db, obj_in=user_in)
    if is_approved:
        statement = (
            update(User).where(User.email == user.email).values(is_approved=True)
        )
        with db as session:
            session.execute(statement)
            session.commit()
    if is_superuser:
        statement = (
            update(User).where(User.email == user.email).values(is_superuser=True)
        )
        with db as session:
            session.execute(statement)
            session.commit()
    if not token:
        statement = (
            update(User).where(User.email == user.email).values(is_email_confirmed=True)
        )
        with db as session:
            session.execute(statement)
            session.commit()
    else:
        crud.user.create_single_use_token(
            db,
            obj_in=SingleUseTokenCreate(
                token=security.get_token_hash(token, salt="confirm")
            ),
            user_id=user.id,
        )
    user_in_db = crud.user.get(db, id=user.id)
    if user_in_db:
        return user_in_db
    else:
        raise Exception("Unable to find user in db")


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> str:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = "testuserpassword"
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user = create_user(db, email, password=password)

    user_in_update = UserUpdate(is_approved=True)
    user = crud.user.update(db, db_obj=user, obj_in=user_in_update)
    return login_and_get_access_token(client=client, email=email, password=password)


def authentication_api_key_from_email(
    *, client: TestClient, email: str, db: Session
) -> str:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = "testuserpassword"
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user = create_user(db, email, password=password)

    user_in_update = UserUpdate(is_approved=True)
    user = crud.user.update(db, db_obj=user, obj_in=user_in_update)
    # create api key for user
    api_key = crud.api_key.create_with_user(db, user_id=user.id)
    return api_key.api_key
