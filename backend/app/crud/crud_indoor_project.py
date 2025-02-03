import logging
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.indoor_project import IndoorProject
from app.models.utils.utcnow import utcnow
from app.schemas.indoor_project import IndoorProjectCreate, IndoorProjectUpdate


logger = logging.getLogger("__name__")


class CRUDIndoorProject(
    CRUDBase[IndoorProject, IndoorProjectCreate, IndoorProjectUpdate]
):
    def create_with_owner(
        self, db: Session, obj_in: IndoorProjectCreate, owner_id: UUID
    ) -> IndoorProject:
        """Create new indoor project.

        Args:
            db (Session): Database session.
            obj_in (IndoorProjectCreate): Creation model with indoor project attributes.
            owner_id (UUID): ID of user creating the indoor project.

        Returns:
            IndoorProject: Newly created indoor project.
        """
        indoor_project = self.model(**obj_in.model_dump(), owner_id=owner_id)

        with db as session:
            session.add(indoor_project)
            session.commit()
            session.refresh(indoor_project)

        return indoor_project

    def read_by_user_id(
        self, db: Session, indoor_project_id: UUID, user_id: UUID
    ) -> Optional[IndoorProject]:
        """Read existing indoor project owned by user.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            user_id (UUID): ID of user indoor project must belong to.

        Returns:
            Optional[IndoorProject]: Indoor project owned by user.
        """
        statement = select(IndoorProject).where(
            and_(
                IndoorProject.id == indoor_project_id,
                IndoorProject.owner_id == user_id,
                IndoorProject.is_active,
            )
        )

        with db as session:
            indoor_project = session.scalar(statement)

            return indoor_project

    def read_multi_by_user_id(
        self, db: Session, user_id: UUID
    ) -> Sequence[IndoorProject]:
        """Read all existing indoor projects owned by user.

        Args:
            db (Session): Database session.
            user_id (UUID): ID of user indoor projects must belong to.

        Returns:
            Sequence[IndoorProject]: All indoor projects owned by user.
        """
        statement = select(IndoorProject).where(
            and_(IndoorProject.owner_id == user_id, IndoorProject.is_active)
        )

        with db as session:
            indoor_projects = session.scalars(statement).all()

            return indoor_projects

    def deactivate(
        self, db: Session, indoor_project_id: UUID
    ) -> Optional[IndoorProject]:
        """Deactivate existing indoor project.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID for indoor project being deactivated.

        Returns:
            Optional[IndoorProject]: Updated indoor project.
        """
        statement = select(IndoorProject).where(
            and_(IndoorProject.id == indoor_project_id, IndoorProject.is_active)
        )

        with db as session:
            indoor_project = session.scalar(statement)

            if indoor_project:
                indoor_project.is_active = False
                indoor_project.deactivated_at = utcnow()
                session.commit()
                session.refresh(indoor_project)

            return indoor_project


indoor_project = CRUDIndoorProject(IndoorProject)
