from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.file_permission import FilePermissionCreate
from app.tests.utils.data_product import SampleDataProduct


def create_file_permission(
    db: Session,
    file_id: UUID | None = None,
) -> models.FilePermission:
    if not file_id:
        file_id = SampleDataProduct(db).obj.id
    return crud.file_permission.create_with_data_product(db, file_id=file_id)
