from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.models.project_like import ProjectLike
from app.schemas.project_like import ProjectLikeCreate, ProjectLikeUpdate


class CRUDProjectLike(CRUDBase[ProjectLike, ProjectLikeCreate, ProjectLikeUpdate]):
    def get_by_project_id_and_user_id(
        self, db: Session, project_id: UUID, user_id: UUID
    ) -> Optional[ProjectLike]:
        """Get a project like by project ID and user ID."""
        statement = (
            select(ProjectLike)
            .join(Project)
            .where(
                Project.is_active,
                ProjectLike.project_id == project_id,
                ProjectLike.user_id == user_id,
            )
        )

        with db as session:
            return session.scalar(statement)


project_like = CRUDProjectLike(ProjectLike)
