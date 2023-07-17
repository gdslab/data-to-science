from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project_member import ProjectMember
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate


class CRUDProjectMember(
    CRUDBase[ProjectMember, ProjectMemberCreate, ProjectMemberUpdate]
):
    def create_with_team(
        self,
        db: Session,
        *,
        obj_in: ProjectMemberCreate,
        member_id: UUID,
        project_id: UUID,
    ) -> ProjectMember:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, member_id=member_id, project_id=project_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj


project_member = CRUDProjectMember(ProjectMember)
