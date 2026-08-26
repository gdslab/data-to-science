from sqlalchemy.orm import Session

from app import crud
from app.schemas.annotation_tag import AnnotationTagCreate, AnnotationTagUpdate
from app.tests.utils.annotation import create_annotation
from app.tests.utils.tag import create_tag


def test_create_annotation_tag(db: Session) -> None:
    annotation = create_annotation(db)
    tag_name = "test-tag"
    annotation_tag_in = AnnotationTagCreate(tag=tag_name)
    annotation_tag = crud.annotation_tag.create_with_annotation(
        db=db, obj_in=annotation_tag_in, annotation_id=annotation.id
    )
    assert annotation_tag.annotation_id == annotation.id
    assert annotation_tag.tag.name == tag_name


def test_read_annotation_tag(db: Session) -> None:
    annotation = create_annotation(db)
    tag_name = "read-test-tag"
    annotation_tag_in = AnnotationTagCreate(tag=tag_name)
    created = crud.annotation_tag.create_with_annotation(
        db=db, obj_in=annotation_tag_in, annotation_id=annotation.id
    )
    results = crud.annotation_tag.get_multi_by_annotation_id(
        db=db, annotation_id=annotation.id
    )
    assert any(row.id == created.id for row in results)


def test_update_annotation_tag(db: Session) -> None:
    annotation = create_annotation(db)
    create_tag(db, name="tag-a")
    tag_b = create_tag(db, name="tag-b")
    created = crud.annotation_tag.create_with_annotation(
        db=db,
        obj_in=AnnotationTagCreate(tag="tag-a"),
        annotation_id=annotation.id,
    )
    # Update to point to tag-b
    updated = crud.annotation_tag.update(
        db=db, db_obj=created, obj_in=AnnotationTagUpdate(tag_id=tag_b.id)
    )
    assert updated.tag_id == tag_b.id


def test_delete_annotation_tag(db: Session) -> None:
    annotation = create_annotation(db)
    tag_name = "delete-test-tag"
    created = crud.annotation_tag.create_with_annotation(
        db=db,
        obj_in=AnnotationTagCreate(tag=tag_name),
        annotation_id=annotation.id,
    )
    deleted = crud.annotation_tag.remove(db=db, id=created.id)
    assert deleted and deleted.id == created.id
    results = crud.annotation_tag.get_multi_by_annotation_id(
        db=db, annotation_id=annotation.id
    )
    assert all(row.id != created.id for row in results)
