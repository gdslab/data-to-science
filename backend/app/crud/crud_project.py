from typing import Sequence, Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: ProjectCreate,
        owner_id: UUID,
        team_id: UUID | None = None,
    ) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        if team_id:
            db_obj = self.model(**obj_in_data, owner_id=owner_id, team_id=team_id)
        else:
            db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Project]:
        statement = (
            select(self.model)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        db_obj = db.scalars(statement).all()
        return db_obj

    def get_multi_by_team(
        self, db: Session, *, team_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Project]:
        statement = (
            select(self.model)
            .filter(Project.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        db_obj = db.scalars(statement).all()
        return db_obj


project = CRUDProject(Project)
