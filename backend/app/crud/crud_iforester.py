from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.iforester import IForester
from app.schemas.iforester import IForesterCreate, IForesterUpdate


class CRUDIForester(CRUDBase[IForester, IForesterCreate, IForesterUpdate]):
    def create_iforester(
        self, db: Session, iforester_in: IForesterCreate, project_id: UUID4
    ) -> IForester:
        # serialize data
        iforester_json = jsonable_encoder(iforester_in)
        # create iforester object
        db_obj = IForester(**iforester_json, project_id=project_id)
        # add object to database
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_iforester_by_id(
        self, db: Session, iforester_id: UUID4, project_id: UUID4
    ) -> Optional[IForester]:
        # query for selecting record by id
        statement = select(IForester).where(
            and_(IForester.id == iforester_id, IForester.project_id == project_id)
        )
        # execute query
        with db as session:
            iforester = session.scalar(statement)
            return iforester

    def get_multi_iforester_by_project_id(
        self, db: Session, project_id: UUID4
    ) -> List[IForester]:
        # query for selecting multi iforester records from single project
        statement = select(IForester).where(IForester.project_id == project_id)
        # execute query
        with db as session:
            iforesters = session.scalars(statement).all()
            return iforesters

    def update_iforester_by_id(
        self,
        db: Session,
        iforester_in: IForesterUpdate,
        iforester_id: UUID4,
        project_id: UUID4,
    ) -> Optional[IForester]:
        # query for selecting current record by id
        statement = select(IForester).where(
            and_(IForester.id == iforester_id, IForester.project_id == project_id)
        )
        # execute query to retrieve current record
        with db as session:
            iforester = session.scalar(statement)
            # update record (if found)
            if iforester:
                iforester_json = jsonable_encoder(iforester_in)
                updated_iforester = crud.iforester.update(
                    db, db_obj=iforester, obj_in=iforester_json
                )
                return updated_iforester
            else:
                return None

    def remove_iforester_by_id(
        self, db: Session, iforester_id: UUID4, project_id: UUID4
    ) -> Optional[IForester]:
        # verify iforester record exists and belongs to project
        iforester = self.get_iforester_by_id(
            db, iforester_id=iforester_id, project_id=project_id
        )
        if iforester:
            # remove record from database using base remove method
            iforester_removed = crud.iforester.remove(db, id=iforester_id)
            return iforester_removed
        else:
            return None


iforester = CRUDIForester(IForester)
