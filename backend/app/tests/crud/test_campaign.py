from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.campaign import CampaignUpdate
from app.tests.utils.campaign import create_campaign
from app.tests.utils.project import create_project
from app.tests.conftest import pytest_requires_campaigns
from app.tests.utils.user import create_user


@pytest_requires_campaigns
def test_create_campaign(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    campaign = create_campaign(db, lead_id=user.id, project_id=project.id)
    assert campaign
    assert campaign.project_id == project.id
    assert campaign.lead_id == user.id
    assert campaign.is_active
    assert campaign.deactivated_at is None


@pytest_requires_campaigns
def test_create_multiple_campaigns_in_same_project(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    campaign = create_campaign(db, project_id=project.id, lead_id=user.id)
    # unique contraint limits project to single campaign obj
    with pytest.raises(IntegrityError):
        campaign2 = create_campaign(db, project_id=project.id, lead_id=user.id)


@pytest_requires_campaigns
def test_read_campaign(db: Session) -> None:
    project = create_project(db)
    campaign = create_campaign(db, project_id=project.id)
    campaign_in_db = crud.campaign.get_campaign_by_id(
        db, project_id=project.id, campaign_id=campaign.id
    )
    assert campaign_in_db
    assert campaign_in_db.project_id == project.id
    assert campaign_in_db.id == campaign.id


@pytest_requires_campaigns
def test_read_campaign_by_project_id(db: Session) -> None:
    project = create_project(db)
    campaign = create_campaign(db, project_id=project.id)
    campaign_in_db = crud.campaign.get_campaign_by_project_id(db, project_id=project.id)
    assert campaign_in_db
    assert campaign_in_db.project_id == project.id
    assert campaign_in_db.id == campaign.id


@pytest_requires_campaigns
def test_read_campaign_by_project_id_without_campaign(db: Session) -> None:
    project = create_project(db)
    campaign_in_db = crud.campaign.get_campaign_by_project_id(db, project_id=project.id)
    assert campaign_in_db is None


@pytest_requires_campaigns
def test_read_campaign_ignores_deactivated_campaigns(db: Session) -> None:
    project = create_project(db)
    campaign = create_campaign(db, project_id=project.id)
    crud.campaign.deactivate(db, project_id=project.id, campaign_id=campaign.id)
    deactivated_campaign = crud.campaign.get_campaign_by_id(
        db, project_id=project.id, campaign_id=campaign.id
    )
    assert not deactivated_campaign


@pytest_requires_campaigns
def test_update_campaign(db: Session) -> None:
    old_campaign_lead = create_user(db)
    project = create_project(db, owner_id=old_campaign_lead.id)
    campaign = create_campaign(db, project_id=project.id, lead_id=old_campaign_lead.id)
    new_campaign_lead = create_user(db)
    campaign_in_update = CampaignUpdate(lead_id=new_campaign_lead.id)
    updated_campaign = crud.campaign.update(
        db, db_obj=campaign, obj_in=campaign_in_update
    )
    assert updated_campaign
    assert updated_campaign.lead_id == new_campaign_lead.id


@pytest_requires_campaigns
def test_deactivate_campaign(db: Session) -> None:
    project = create_project(db)
    campaign = create_campaign(db, project_id=project.id)
    campaign2 = crud.campaign.deactivate(
        db, project_id=project.id, campaign_id=campaign.id
    )
    campaign3 = crud.campaign.get(db, id=campaign.id)
    assert campaign2 and campaign3
    assert campaign3.id == campaign.id
    assert not campaign3.is_active
    assert isinstance(campaign3.deactivated_at, datetime)
    assert campaign3.deactivated_at < datetime.now(tz=timezone.utc)
