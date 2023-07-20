from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: ProjectCreate,
        owner_id: UUID,
    ) -> Project:
        """Create new project and add user as project member."""
        # add project to db
        obj_in_data = jsonable_encoder(obj_in)
        project_db_obj = self.model(
            **obj_in_data,
            owner_id=owner_id,
        )
        with db as session:
            session.add(project_db_obj)
            session.commit()
            session.refresh(project_db_obj)
        # add project memeber to db
        member_db_obj = ProjectMember(member_id=owner_id, project_id=project_db_obj.id)
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(member_db_obj)
        return project_db_obj

    def get_user_project_list(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Project]:
        """List of projects the user belongs to."""
        statement = (
            select(Project)
            .join(ProjectMember.project)
            .where(ProjectMember.member_id == user_id)
        )
        with db as session:
            db_obj = session.scalars(statement).all()
            # indicate if project member is also project owner
            for project in db_obj:
                setattr(project, "is_owner", user_id == project.owner_id)
        return db_obj


project = CRUDProject(Project)
