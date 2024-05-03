from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import get_current_user
from app.core.config import settings


def test_get_site_statistics_with_non_superuser(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/admin/site_statistics")
    assert response.status_code == status.HTTP_403_FORBIDDEN
