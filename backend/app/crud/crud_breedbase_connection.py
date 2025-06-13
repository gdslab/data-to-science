import logging
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.breedbase_connection import BreedbaseConnection
from app.models.project import Project
from app.schemas.breedbase_connection import (
    BreedbaseConnectionCreate,
    BreedbaseConnectionUpdate,
)


logger = logging.getLogger(__name__)


class CRUDBreedbaseConnection(
    CRUDBase[BreedbaseConnection, BreedbaseConnectionCreate, BreedbaseConnectionUpdate]
):
    def create_with_project(
        self, db: Session, *, obj_in: BreedbaseConnectionCreate, project_id: UUID
    ) -> BreedbaseConnection:
        """Create a breedbase connection with a project."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = BreedbaseConnection(**obj_in_data, project_id=project_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def get_by_study_id(
        self, db: Session, study_id: str, user_id: UUID
    ) -> Sequence[BreedbaseConnection]:
        """Get breedbase connections by trial ID, ensuring user has access to the projects."""
        statement = (
            select(BreedbaseConnection)
            .distinct()
            .join(Project)
            .join(Project.members)
            .where(
                BreedbaseConnection.study_id == study_id,
                Project.is_active,
                Project.members.any(member_id=user_id),
            )
        )

        with db as session:
            return session.scalars(statement).all()

    def get_multi_by_project_id(
        self, db: Session, project_id: UUID
    ) -> Sequence[BreedbaseConnection]:
        """Get all breedbase connections by project ID."""
        statement = (
            select(BreedbaseConnection)
            .join(Project)
            .where(BreedbaseConnection.project_id == project_id, Project.is_active)
        )

        with db as session:
            return session.scalars(statement).all()


breedbase_connection = CRUDBreedbaseConnection(BreedbaseConnection)
