from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.dataset import Dataset
from app.models.project import Project
from app.schemas.dataset import DatasetCreate, DatasetUpdate


class CRUDDataset(CRUDBase[Dataset, DatasetCreate, DatasetUpdate]):
    def create_with_project(
        self,
        db: Session,
        *,
        obj_in: DatasetCreate,
        project_id: UUID,
    ) -> Dataset:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, project_id=project_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_user_dataset(
        self,
        db: Session,
        *,
        dataset_id: UUID,
        project_id: UUID,
    ) -> Dataset | None:
        statement = (
            select(self.model)
            .join(Project.datasets)
            .where(Project.id == project_id)
            .where(self.model.id == dataset_id)
        )
        with db as session:
            db_obj = session.scalars(statement).one_or_none()
        return db_obj

    def get_project_dataset_list(
        self, db: Session, *, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Dataset]:
        """List of datasets belonging to a project."""
        statement = (
            select(self.model)
            .filter(self.model.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        with db as session:
            db_obj = session.scalars(statement).all()
        return db_obj


dataset = CRUDDataset(Dataset)
