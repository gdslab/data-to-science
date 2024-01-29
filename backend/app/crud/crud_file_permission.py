from datetime import datetime
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.file_permission import FilePermission
from app.schemas.file_permission import FilePermissionCreate, FilePermissionUpdate


class CRUDFilePermission(
    CRUDBase[FilePermission, FilePermissionCreate, FilePermissionUpdate]
):
    def create_with_data_product(self, db: Session, file_id: UUID):
        file_permission_in = {}
        file_permission = self.model(**file_permission_in, file_id=file_id)
        with db as session:
            session.add(file_permission)
            session.commit()
            session.refresh(file_permission)
        return file_permission

    def get_by_data_product(self, db: Session, file_id: UUID) -> FilePermission | None:
        statement = select(FilePermission).where(FilePermission.file_id == file_id)
        with db as session:
            file_permission = session.scalar(statement)
            # update last accessed timestamp
            if file_permission:
                crud.file_permission.update(
                    db,
                    db_obj=file_permission,
                    obj_in=FilePermissionUpdate(last_accessed_at=datetime.now()),
                )
            return file_permission

    def get_by_filename(self, db: Session, filename: str) -> FilePermission | None:
        statement = (
            select(FilePermission)
            .join(DataProduct)
            .where(func.lower(DataProduct.filepath).contains(filename))
        )
        with db as session:
            file_permission = session.scalar(statement)
            # update last accessed timestamp
            if file_permission:
                crud.file_permission.update(
                    db,
                    db_obj=file_permission,
                    obj_in=FilePermissionUpdate(last_accessed_at=datetime.now()),
                )
            return file_permission


file_permission = CRUDFilePermission(FilePermission)
