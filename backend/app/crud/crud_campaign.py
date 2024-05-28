from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.campaign import Campaign
from app.models.project import Project
from app.models.utils.user import utcnow
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CRUDCampaign(CRUDBase[Campaign, CampaignCreate, CampaignUpdate]):
    def create_with_project(
        self, db: Session, obj_in: CampaignCreate, project_id: UUID
    ) -> Campaign:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Campaign(**obj_in_data, project_id=project_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_campaign_by_id(
        self, db: Session, project_id: UUID, campaign_id: UUID
    ) -> Campaign | None:
        statement = (
            select(Campaign)
            .where(Campaign.project_id == project_id)
            .where(Campaign.id == campaign_id)
            .where(Campaign.is_active)
        )
        with db as session:
            campaign = session.scalar(statement)
            return campaign

    def get_campaign_by_project_id(
        self, db: Session, project_id: UUID
    ) -> Campaign | None:
        statement = (
            select(Campaign)
            .where(Campaign.project_id == project_id)
            .where(Campaign.is_active)
        )
        with db as session:
            campaign = session.scalar(statement)
            return campaign

    # Not current used. Projects can only have a single campaign record.
    # def get_multi_by_project(
    #     self, db: Session, project_id: UUID, skip: int = 0, limit: int = 100
    # ) -> Sequence[Campaign]:
    #     statement = (
    #         select(Campaign)
    #         .where(Campaign.project_id == project_id)
    #         .where(Campaign.is_active)
    #     )
    #     with db as session:
    #         campaigns = session.scalars(statement).all()
    #         return campaigns

    def update_campaign_by_id(
        self,
        db: Session,
        project_id: UUID,
        campaign_id: UUID,
        campaign_in: CampaignUpdate,
    ) -> Campaign | None:
        statement = (
            select(Campaign)
            .where(Campaign.project_id == project_id)
            .where(Campaign.id == campaign_id)
            .where(Campaign.is_active)
        )
        with db as session:
            campaign = session.scalar(statement)
            if campaign:
                if campaign_in.lead_id:
                    # check if lead_id is associated with project member
                    lead_user = crud.project_member.get_by_project_and_member_id(
                        db, project_id=project_id, member_id=campaign_in.lead_id
                    )
                    if not lead_user:
                        return None
                updated_campaign = crud.campaign.update(
                    db, db_obj=campaign, obj_in=campaign_in
                )
                return updated_campaign
            else:
                return None

    def deactivate(
        self, db: Session, project_id: UUID, campaign_id: UUID
    ) -> Campaign | None:
        # update campaign is_active to false and set deactivated datetime
        statement = (
            update(Campaign)
            .where(Campaign.project_id == project_id)
            .where(Campaign.id == campaign_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(statement)
            session.commit()
        # get updated campaign
        statement = select(Campaign).where(Campaign.id == campaign_id)
        with db as session:
            deactivated_campaign = session.scalar(statement)
            return deactivated_campaign


campaign = CRUDCampaign(Campaign)
