from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.upload import Upload
from app.schemas.upload import UploadCreate, UploadUpdate


class CRUDUpload(CRUDBase[Upload, UploadCreate, UploadUpdate]):
    def create_with_user(
        self, db: Session, upload_id: str, user_id: UUID, is_uploading: bool = True
    ) -> Upload:
        """Create new upload event.

        Args:
            db (Session): Database session.
            upload_id (str): Upload event ID from tusd.
            user_id (UUID): ID of user uploading file.
            is_uploading (bool, optional): Current status of upload. Defaults to True.

        Returns:
            Upload: Newly created upload instance.
        """
        upload_in = UploadCreate(
            upload_id=upload_id, user_id=user_id, is_uploading=is_uploading
        )
        upload = self.model(**upload_in.model_dump())
        with db as session:
            session.add(upload)
            session.commit()
            session.refresh(upload)

        return upload

    def get_upload_by_upload_id(self, db: Session, upload_id: str) -> Upload | None:
        """Find upload record by unique upload ID.

        Args:
            db (Session): Database session
            upload_id (str): Upload event ID from tusd.

        Returns:
            Upload | None: Upload record or None if record matching ID not found.
        """
        statement = select(Upload).where(Upload.upload_id == upload_id)
        with db as session:
            upload = session.scalar(statement)
            return upload


upload = CRUDUpload(Upload)
