from uuid import UUID

from fastapi.encoders import jsonable_encoder
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


team_member = CRUDTeamMember(TeamMember)
