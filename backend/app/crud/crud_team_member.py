from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.team_member import TeamMember
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    def create_with_team(
        self,
        db: Session,
        *,
        obj_in: TeamMemberCreate,
        member_id: UUID,
        team_id: UUID,
    ) -> TeamMember:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, member_id=member_id, team_id=team_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_user_team_member(
        self, db: Session, *, user_id: UUID, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record for user by team id."""
        statement = (
            select(TeamMember)
            .where(TeamMember.member_id == user_id)
            .where(TeamMember.team_id == team_id)
        )
        with db as session:
            db_obj = session.scalars(statement).one_or_none()
        return db_obj

    def get_list_of_team_members(
        self, db: Session, *, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[TeamMember]:
        statement = select(TeamMember).where(TeamMember.team_id == team_id)
        with db as session:
            db_obj = session.scalars(statement).all()
        return db_obj


team_member = CRUDTeamMember(TeamMember)
