from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project_member import ProjectMember
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate


class CRUDProjectMember(
    CRUDBase[ProjectMember, ProjectMemberCreate, ProjectMemberUpdate]
):
    def create_with_project(
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

    def get_list_of_project_members(
        self, db: Session, *, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ProjectMember]:
        statement = select(ProjectMember).where(ProjectMember.project_id == project_id)
        with db as session:
            db_obj = session.scalars(statement).all()
        return db_obj


project_member = CRUDProjectMember(ProjectMember)