import os
from datetime import datetime
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.conftest import pytest_requires_campaigns
from app.models.utils.campaign import is_uuid
from app.schemas.role import Role
from app.tests.utils.campaign import (
    create_campaign,
    get_filename_from_content_disposition_header,
)
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


PROJECTS_API_URL = f"{settings.API_V1_STR}/projects"


@pytest_requires_campaigns
def test_create_campaign_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    response = client.post(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert is_uuid(response_data["id"])
    assert response_data["lead_id"] == str(current_user.id)
    assert response_data["is_active"]
    assert response_data["deactivated_at"] is None


@pytest_requires_campaigns
def test_create_campaign_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    response = client.post(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_201_CREATED


@pytest_requires_campaigns
def test_create_campaign_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    response = client.post(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_campaigns
def test_create_campaign_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    response = client.post(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_read_campaign_by_project_id_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id, lead_id=current_user.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)
    assert response_data["lead_id"] == str(current_user.id)


@pytest_requires_campaigns
def test_read_campaign_by_project_id_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id, lead_id=project_owner.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)
    assert response_data["lead_id"] == str(project_owner.id)


@pytest_requires_campaigns
def test_read_campaign_by_project_id_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id, lead_id=project_owner.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)
    assert response_data["lead_id"] == str(project_owner.id)


@pytest_requires_campaigns
def test_read_campaign_by_project_id_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    campaign = create_campaign(db, project_id=project.id, lead_id=project_owner.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_read_campaign_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)


@pytest_requires_campaigns
def test_read_campaign_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)


@pytest_requires_campaigns
def test_read_campaign_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)


@pytest_requires_campaigns
def test_read_campaign_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    campaign = create_campaign(db, project_id=project.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_read_campaign_returns_none_for_deactivated_campaign(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id)
    crud.campaign.deactivate(db, project_id=project.id, campaign_id=campaign.id)
    response = client.get(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_update_campaign_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id, lead_id=current_user.id)
    # create user that will be new lead
    new_lead_user = create_user(db)
    # add user as project member
    create_project_member(db, member_id=new_lead_user.id, project_id=project.id)
    update_data = jsonable_encoder({"lead_id": new_lead_user.id})
    response = client.put(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)
    assert response_data["lead_id"] != str(current_user.id)
    assert response_data["lead_id"] == str(new_lead_user.id)


@pytest_requires_campaigns
def test_update_campaign_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    # create user that will be new lead
    new_lead_user = create_user(db)
    # add user as project member
    create_project_member(db, member_id=new_lead_user.id, project_id=project.id)
    update_data = jsonable_encoder({"lead_id": new_lead_user.id})
    response = client.put(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK


@pytest_requires_campaigns
def test_update_campaign_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    # create user that will be new lead
    new_lead_user = create_user(db)
    # add user as project member
    create_project_member(db, member_id=new_lead_user.id, project_id=project.id)
    update_data = jsonable_encoder({"lead_id": new_lead_user.id})
    response = client.put(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}", json=update_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_campaigns
def test_update_campaign_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    campaign = create_campaign(db, project_id=project.id)
    # create user that will be new lead
    new_lead_user = create_user(db)
    # add user as project member
    create_project_member(db, member_id=new_lead_user.id, project_id=project.id)
    update_data = jsonable_encoder({"lead_id": new_lead_user.id})
    response = client.put(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}", json=update_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_deactivate_campaign_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id)
    response = client.delete(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(campaign.id)
    assert response_data["is_active"] is False
    try:
        deactivated_at = datetime.strptime(
            response_data["deactivated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        assert isinstance(deactivated_at, datetime)
    except Exception:
        raise


@pytest_requires_campaigns
def test_deactivate_campaign_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    response = client.delete(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_campaigns
def test_deactivate_campaign_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id)
    response = client.delete(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_campaigns
def test_deactivate_campaign_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    campaign = create_campaign(db, project_id=project.id)
    response = client.delete(f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_campaigns
def test_download_campaign_template_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    campaign = create_campaign(db, project_id=project.id, include_form_data=True)
    data = {"timepoints": [{"measurement": 0, "treatment": 0, "timepoint": 0}]}
    response = client.post(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}/download", json=data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-disposition")

    header = response.headers["content-disposition"]
    filename = get_filename_from_content_disposition_header(header)
    assert filename

    path_to_static_file = f"{settings.TEST_STATIC_DIR}/projects/{project.id}/campaigns/{campaign.id}/{filename}"
    assert os.path.exists(path_to_static_file)


@pytest_requires_campaigns
def test_download_campaign_template_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id, include_form_data=True)
    data = {"timepoints": [{"measurement": 0, "treatment": 0, "timepoint": 0}]}
    response = client.post(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}/download", json=data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-disposition")

    header = response.headers["content-disposition"]
    filename = get_filename_from_content_disposition_header(header)
    assert filename

    path_to_static_file = f"{settings.TEST_STATIC_DIR}/projects/{project.id}/campaigns/{campaign.id}/{filename}"
    assert os.path.exists(path_to_static_file)


@pytest_requires_campaigns
def test_download_campaign_template_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project_owner = create_user(db)
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=project_owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    campaign = create_campaign(db, project_id=project.id, include_form_data=True)
    data = {"timepoints": [{"measurement": 0, "treatment": 0, "timepoint": 0}]}
    response = client.post(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}/download", json=data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-disposition")

    header = response.headers["content-disposition"]
    filename = get_filename_from_content_disposition_header(header)
    assert filename

    path_to_static_file = f"{settings.TEST_STATIC_DIR}/projects/{project.id}/campaigns/{campaign.id}/{filename}"
    assert os.path.exists(path_to_static_file)


@pytest_requires_campaigns
def test_download_campaign_template_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    campaign = create_campaign(db, project_id=project.id, include_form_data=True)
    data = {"timepoints": [{"measurement": 0, "treatment": 0, "timepoint": 0}]}
    response = client.post(
        f"{PROJECTS_API_URL}/{project.id}/campaigns/{campaign.id}/template", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
