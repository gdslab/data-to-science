from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB, UserUpdate
from app.tests.utils.utils import random_email, random_full_name, random_password


def user_authenticate_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    """Generate authorization header for provided user credentials."""
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/auth/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}    
    return headers


def create_random_user_in(email: str | None = None) -> UserCreate:
    """Create random user model with specific email if provided."""
    if not email:
        email = random_email()
    password = random_password()
    full_name = random_full_name()
    user_in = UserCreate(
        email=email,
        password=password,
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    return user_in


def create_random_user(db: Session, email: str | None = None) -> User:
    """Create random user in database with specific email if provided."""
    user_in = create_random_user_in(email)
    user = crud.user.create(db=db, obj_in=user_in)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
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
    
    return user_authenticate_headers(client=client, email=email, password=password)
