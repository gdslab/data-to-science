from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate


class CRUDGroup(CRUDBase[Group, GroupCreate, GroupUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: GroupCreate, owner_id: int) -> Group:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100) -> list[Group]:
        return (
            db.query(self.model)
            .filter(Group.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


group = CRUDGroup(Group)
