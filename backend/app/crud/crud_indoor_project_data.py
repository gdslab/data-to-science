import logging
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.indoor_project_data import IndoorProjectData
from app.models.utils.utcnow import utcnow
from app.schemas.indoor_project_data import (
    IndoorProjectDataCreate,
    IndoorProjectDataUpdate,
)


logger = logging.getLogger("__name__")


class CRUDIndoorProjectData(
    CRUDBase[IndoorProjectData, IndoorProjectDataCreate, IndoorProjectDataUpdate]
):
    def create_with_indoor_project(
        self,
        db: Session,
        obj_in: IndoorProjectDataCreate,
        indoor_project_id: UUID,
        uploader_id: UUID,
    ) -> IndoorProjectData:
        """Create new indoor project data.

        Args:
            db (Session): Database session.
            obj_in (IndoorDataCreate): Creation model with indoor data attributes.
            indoor_project_id (UUID): ID of indoor project associated with data.
            uploader_id (UUID): ID of user uploading the data.

        Returns:
            IndoorData: Newly created indoor project data.
        """
        indoor_project_data = self.model(
            **obj_in.model_dump(),
            indoor_project_id=indoor_project_id,
            uploader_id=uploader_id
        )

        with db as session:
            session.add(indoor_project_data)
            session.commit()
            session.refresh(indoor_project_data)

        return indoor_project_data

    def read_by_id(
        self, db: Session, indoor_project_id: UUID, indoor_project_data_id: UUID
    ) -> Optional[IndoorProjectData]:
        """Read existing indoor project data belonging to indoor project.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            indoor_project_data_id (UUID): ID of indoor project data.

        Returns:
            Optional[IndoorProjectData]: Indoor project data.
        """
        statement = select(IndoorProjectData).where(
            and_(
                IndoorProjectData.indoor_project_id == indoor_project_id,
                IndoorProjectData.id == indoor_project_data_id,
                IndoorProjectData.is_active,
            )
        )

        with db as session:
            indoor_project_data = session.scalar(statement)

            return indoor_project_data

    def read_multi_by_id(
        self, db: Session, indoor_project_id: UUID, file_type: Optional[str] = None
    ) -> Sequence[IndoorProjectData]:
        """Read all existing indoor project data belonging to indoor project.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            file_type (Optional[str]): Type of file (e.g., .tar or .xlsx).

        Returns:
            Sequence[IndoorProjectData]: List of indoor project data.
        """
        conditions = [
            IndoorProjectData.indoor_project_id == indoor_project_id,
            IndoorProjectData.is_active,
        ]

        if file_type:
            conditions.append(IndoorProjectData.file_type == file_type)

        statement = select(IndoorProjectData).where(and_(*conditions))

        with db as session:
            indoor_project_data = session.scalars(statement).all()

            return indoor_project_data

    def deactivate(
        self, db: Session, indoor_project_id: UUID, indoor_project_data_id: UUID
    ) -> Optional[IndoorProjectData]:
        """Deactivate indoor project data.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            indoor_project_data_id (UUID): ID of indoor project data.

        Returns:
            Optional[IndoorProjectData]: Updated indoor project data.
        """
        statement = select(IndoorProjectData).where(
            and_(
                IndoorProjectData.indoor_project_id == indoor_project_id,
                IndoorProjectData.id == indoor_project_data_id,
                IndoorProjectData.is_active,
            )
        )

        with db as session:
            indoor_project_data = session.scalar(statement)

            if indoor_project_data:
                indoor_project_data.is_active = False
                indoor_project_data.deactivated_at = utcnow()
                session.commit()
                session.refresh(indoor_project_data)

            return indoor_project_data


indoor_project_data = CRUDIndoorProjectData(IndoorProjectData)
