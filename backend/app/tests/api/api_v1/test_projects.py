from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.tests.utils.location import create_random_location
from app.tests.utils.user import create_random_user
from app.tests.utils.project import (
    create_random_project,
    random_planting_date,
    random_harvest_date,
)
from app.tests.utils.project_member import create_random_project_member
from app.tests.utils.team import random_team_name, random_team_description


def test_create_project(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Verify new project is created in database."""
    location = create_random_location(db)
    data = jsonable_encoder(
        {
            "title": random_team_name(),
            "description": random_team_description(),
            "planting_date": random_planting_date(),
            "harvest_date": random_harvest_date(),
            "location_id": location.id,
        }
    )
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert 201 == r.status_code
    content = r.json()
    assert "id" in content
    assert data["title"] == content["title"]
    assert data["description"] == content["description"]
    assert data["planting_date"] == content["planting_date"]
    assert data["harvest_date"] == content["harvest_date"]
