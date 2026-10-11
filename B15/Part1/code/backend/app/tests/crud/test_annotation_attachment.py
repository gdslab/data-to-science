from sqlalchemy.orm import Session

from app import crud
from app.schemas.annotation_attachment import (
    AnnotationAttachmentCreate,
    AnnotationAttachmentUpdate,
)
from app.tests.utils.annotation import create_annotation


def test_create_annotation_attachment(db: Session) -> None:
    annotation = create_annotation(db)
    attachment_in = AnnotationAttachmentCreate(
        original_filename="image.jpg",
        filepath="/tmp/image.jpg",
        content_type="image/jpeg",
        size_bytes=1234,
        width_px=None,
        height_px=None,
        duration_seconds=None,
    )
    attachment = crud.annotation_attachment.create_with_annotation(
        db=db, obj_in=attachment_in, annotation_id=annotation.id
    )
    assert attachment.annotation_id == annotation.id
    assert attachment.original_filename == "image.jpg"


def test_read_annotation_attachment(db: Session) -> None:
    annotation = create_annotation(db)
    created = crud.annotation_attachment.create_with_annotation(
        db=db,
        obj_in=AnnotationAttachmentCreate(
            original_filename="file.bin",
            filepath="/tmp/file.bin",
            content_type="application/octet-stream",
            size_bytes=10,
            width_px=None,
            height_px=None,
            duration_seconds=None,
        ),
        annotation_id=annotation.id,
    )
    results = crud.annotation_attachment.get_multi_by_annotation_id(
        db=db, annotation_id=annotation.id
    )
    assert any(att.id == created.id for att in results)


def test_update_annotation_attachment(db: Session) -> None:
    annotation = create_annotation(db)
    created = crud.annotation_attachment.create_with_annotation(
        db=db,
        obj_in=AnnotationAttachmentCreate(
            original_filename="video.mp4",
            filepath="/tmp/video.mp4",
            content_type="video/mp4",
            size_bytes=100,
            width_px=None,
            height_px=None,
            duration_seconds=None,
        ),
        annotation_id=annotation.id,
    )
    update_in = AnnotationAttachmentUpdate(width_px=1920, height_px=1080)
    updated = crud.annotation_attachment.update(
        db=db,
        db_obj=created,
        obj_in=update_in,
    )
    assert updated.width_px == 1920
    assert updated.height_px == 1080


def test_delete_annotation_attachment(db: Session) -> None:
    annotation = create_annotation(db)
    created = crud.annotation_attachment.create_with_annotation(
        db=db,
        obj_in=AnnotationAttachmentCreate(
            original_filename="audio.wav",
            filepath="/tmp/audio.wav",
            content_type="audio/wav",
            size_bytes=2048,
            width_px=None,
            height_px=None,
            duration_seconds=None,
        ),
        annotation_id=annotation.id,
    )
    deleted = crud.annotation_attachment.remove(db=db, id=created.id)
    assert deleted and deleted.id == created.id
    results = crud.annotation_attachment.get_multi_by_annotation_id(
        db=db, annotation_id=annotation.id
    )
    assert all(att.id != created.id for att in results)
