from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.team import Team
from app.models.team_member import TeamMember
from app.schemas.team import TeamCreate, TeamUpdate


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TeamCreate, owner_id: UUID
    ) -> Team:
        """Create new team and add user as team member."""
        # add team object
        obj_in_data = jsonable_encoder(obj_in)
        team_db_obj = self.model(**obj_in_data, owner_id=owner_id)
        with db as session:
            session.add(team_db_obj)
            session.commit()
            session.refresh(team_db_obj)
        # add as manager of newly created team
        member_db_obj = TeamMember(member_id=owner_id, team_id=team_db_obj.id)
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(member_db_obj)
        return team_db_obj

    def get_user_team(
        self, db: Session, *, user_id: UUID, team_id: UUID, only_owner: bool = False
    ) -> Team | None:
        """Retrieve team by id if user belongs to team."""
        if only_owner:
            statement = select(Team).filter_by(owner_id=user_id)
        else:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
                .where(TeamMember.team_id == team_id)
            )
        with db as session:
            db_obj = session.scalars(statement).one_or_none()
            if db_obj:
                setattr(db_obj, "is_owner", user_id == db_obj.owner_id)

        return db_obj

    def get_user_team_list(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Team]:
        """List of teams the user belongs to."""
        statement = (
            select(Team)
            .join(TeamMember.team)
            .where(TeamMember.member_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        with db as session:
            db_obj = session.scalars(statement).all()
            # indicate if team member is also team owner
            for team in db_obj:
                setattr(team, "is_owner", user_id == team.owner_id)
        return db_obj


team = CRUDTeam(Team)
