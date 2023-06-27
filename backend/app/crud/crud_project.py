from typing import Sequence, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: ProjectCreate, owner_id: int) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_owner_and_group(self, db: Session, *, obj_in: ProjectCreate, owner_id: int, group_id: int) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id, group_id=group_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100) -> Sequence[Project]:
        statement = select(self.model).filter(Project.owner_id == owner_id).offset(skip).limit(limit)
        db_obj = db.scalars(statement).all()
        return db_obj

    def get_multi_by_group(self, db: Session, *, group_id: int, skip: int = 0, limit: int = 100) -> Sequence[Project]:
        statement = select(self.model).filter(Project.group_id == group_id).offset(skip).limit(limit)
        db_obj = db.scalars(statement).all()
        return db_obj


project = CRUDProject(Project)
