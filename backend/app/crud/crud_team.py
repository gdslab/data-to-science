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
        self,
        db: Session,
        *,
        obj_in: TeamCreate,
        owner_id: UUID,
    ) -> Team:
        # add team object
        obj_in_data = jsonable_encoder(obj_in)
        team_db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(team_db_obj)
        db.commit()
        # add as manager of newly created team
        member_db_obj = TeamMember(
            role="Manager", member_id=owner_id, team_id=team_db_obj.id
        )
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(team_db_obj)
        return team_db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Team]:
        statement = (
            select(self.model)
            .filter(Team.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        with db as session:
            db_obj = session.scalars(statement).all()
        return db_obj

    def get_multi_by_member(
        self, db: Session, *, member_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Team]:
        statement = (
            select(Team).join(TeamMember.team).where(TeamMember.member_id == member_id)
        )
        with db as session:
            db_obj = session.scalars(statement).all()
        return db_obj


team = CRUDTeam(Team)
