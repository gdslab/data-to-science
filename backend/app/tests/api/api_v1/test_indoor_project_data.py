from typing import List

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.indoor_project_data import create_indoor_project_data
from app.tests.utils.user import create_user


BASE_API_URL = f"{settings.API_V1_STR}/indoor_projects"


def test_read_indoor_project_data(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test reading multiple indoor project data uploads from an indoor project.
    """
    # create indoor project with current user as owner
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)

    # create indoor project data for indoor project
    indoor_project_dataset1 = create_indoor_project_data(
        db, indoor_project_id=indoor_project.id, uploader_id=current_user.id
    )
    indoor_project_dataset2 = create_indoor_project_data(
        db, indoor_project_id=indoor_project.id, uploader_id=current_user.id
    )

    # get all indoor project data associated with indoor project
    response = client.get(f"{BASE_API_URL}/{indoor_project.id}/uploaded")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, List)
    assert len(response_data) == 2
    for indoor_project_dataset in response_data:
        assert indoor_project_dataset["id"] in [
            str(indoor_project_dataset1.id),
            str(indoor_project_dataset2.id),
        ]
