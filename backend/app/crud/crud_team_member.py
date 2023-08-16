import logging
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Bundle, Session

from app.crud.base import CRUDBase
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate


logger = logging.getLogger("__name__")


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    def create_with_team(
        self, db: Session, *, obj_in: TeamMemberCreate, team_id: UUID
    ) -> TeamMember | None:
        obj_in_data = jsonable_encoder(obj_in)
        email = obj_in_data["email"]
        statement = select(User).filter_by(email=email, is_approved=True)
        with db as session:
            user_obj = session.scalars(statement).one_or_none()
            if user_obj:
                db_obj = self.model(member_id=user_obj.id, team_id=team_id)
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)
            else:
                db_obj = None
        return db_obj

    def get_team_member_by_email(
        self, db: Session, *, email: str, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by email."""
        statement = (
            select(TeamMember)
            .join(User, TeamMember.member)
            .where(User.email == email)
            .where(TeamMember.team_id == team_id)
        )
        with db as session:
            team_member = session.scalars(statement).one_or_none()
        return team_member

    def get_team_member_by_id(
        self, db: Session, *, user_id: UUID, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by team id."""
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
        statement = (
            select(
                TeamMember,
                Bundle("user", User.first_name, User.last_name, User.email),
            )
            .join(User, TeamMember.member)
            .where(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        team_members: list[TeamMember] = []
        with db as session:
            for row in session.execute(statement).all():
                full_name = f"{row.user.first_name} {row.user.last_name}"
                setattr(row[0], "full_name", full_name)
                setattr(row[0], "email", row.user.email)
                team_members.append(row[0])

        return team_members


team_member = CRUDTeamMember(TeamMember)
