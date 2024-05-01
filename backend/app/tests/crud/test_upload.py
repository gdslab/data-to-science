from datetime import datetime

from sqlalchemy.orm import Session

from app import crud
from app.schemas import UploadCreate, UploadUpdate
from app.tests.utils.user import create_user

EXAMPLE_UPLOAD_ID = "7c26cadbb9ab184c35678d180cfa8ad4"


def test_create_upload(db: Session) -> None:
    user = create_user(db)
    upload = crud.upload.create_with_user(
        db, upload_id=EXAMPLE_UPLOAD_ID, user_id=user.id
    )
    assert upload
    assert upload.upload_id == EXAMPLE_UPLOAD_ID
    assert upload.user_id == user.id
    assert upload.is_uploading is True
    assert upload.last_updated_at < datetime.utcnow()


def test_update_upload(db: Session) -> None:
    user = create_user(db)
    upload = crud.upload.create_with_user(
        db, upload_id=EXAMPLE_UPLOAD_ID, user_id=user.id
    )
    ts = datetime.utcnow()
    upload_update_in = UploadUpdate(is_uploading=False, last_updated_at=ts)
    upload_updated = crud.upload.update(db, db_obj=upload, obj_in=upload_update_in)
    assert upload_updated
    assert upload_updated.upload_id == upload.upload_id
    assert upload_updated.is_uploading is False
    assert upload_updated.last_updated_at == ts
