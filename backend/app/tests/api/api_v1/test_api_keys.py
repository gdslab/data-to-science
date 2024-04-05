from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings


def test_request_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/auth/request-api-key")
    assert response.status_code == status.HTTP_200_OK
    user_api_key = crud.api_key.get_by_user(db, user_id=current_user.id)
    assert user_api_key
    assert user_api_key.is_active


def test_revoke_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_200_OK
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert not api_key_in_db.is_active


def test_revoke_api_key_when_one_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_404_NOT_FOUND
