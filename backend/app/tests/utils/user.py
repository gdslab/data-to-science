from fastapi.testclient import TestClient
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


def create_random_user_in(
    email: str | None = None, password: str | None = None
) -> UserCreate:
    """Create random user model with specific email if provided."""
    if not email:
        email = random_email()
    if not password:
        password = random_password()
    full_name = random_full_name()
    user_in = UserCreate(
        email=email,
        password=password,
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    return user_in


def create_random_user(
    db: Session,
    email: str | None = None,
    password: str | None = None,
    is_approved: bool = True,
    token: str | None = None,
    token_expired: bool = False,
) -> User:
    """Create random user in database with specific email if provided."""
    user_in = create_random_user_in(email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    if is_approved:
        statement = (
            update(User).where(User.email == user.email).values(is_approved=True)
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
    password = random_password()
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user = create_random_user(db, email)

    user_in_update = UserUpdate(password=password, is_approved=True)
    user = crud.user.update(db, db_obj=user, obj_in=user_in_update)
    return login_and_get_access_token(client=client, email=email, password=password)
