from sqlalchemy.orm import Session

from app import crud
from app.schemas.annotation import AnnotationUpdate
from app.schemas.annotation_tag import AnnotationTagCreate
from app.tests.utils.annotation import (
    create_annotation,
    create_annotation_in,
    create_multiple_annotations,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.tag import create_tag
from app.tests.utils.user import create_user


def test_create_annotation(db: Session) -> None:
    # Create a data product to associate with the annotation
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation using utility
    annotation = create_annotation(
        db=db,
        description="Test annotation for point geometry",
        geometry_type="Point",
        data_product_id=data_product.id,
    )

    # Attach a tag to the annotation
    tag_name = "point-annotation-tag"
    annotation_tag_in = AnnotationTagCreate(tag=tag_name)
    annotation_tag = crud.annotation_tag.create_with_annotation(
        db=db, obj_in=annotation_tag_in, annotation_id=annotation.id
    )

    # Assertions
    assert annotation.description == "Test annotation for point geometry"
    assert annotation.data_product_id == data_product.id
    assert annotation.id is not None
    assert annotation.created_at is not None
    assert annotation.updated_at is not None
    assert annotation.geom is not None  # Geometry should be stored
    assert annotation.created_by_id is None  # No user specified
    assert annotation_tag.annotation_id == annotation.id
    assert annotation_tag.tag.name == tag_name


def test_create_annotation_with_user(db: Session) -> None:
    # Create a user and data product
    user = create_user(db)
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with user
    annotation = create_annotation(
        db=db,
        description="Test annotation with user",
        geometry_type="Point",
        data_product_id=data_product.id,
        created_by_id=user.id,
    )

    # Assertions
    assert annotation.description == "Test annotation with user"
    assert annotation.data_product_id == data_product.id
    assert annotation.created_by_id == user.id

    # Get annotation with created_by relationship loaded
    annotation_with_user = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_user is not None
    assert annotation_with_user.created_by is not None
    assert annotation_with_user.created_by.id == user.id
    assert annotation_with_user.created_by.email == user.email


def test_get_multi_by_data_product_id(db: Session) -> None:
    # Create a user and data product to associate with annotations
    user = create_user(db)
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create multiple annotations for the same data product
    created_annotations = create_multiple_annotations(
        db=db,
        count=2,
        data_product_id=data_product.id,
        base_description="Test annotation",
        created_by_id=user.id,
    )

    # Test get_multi_by_data_product_id
    annotations = crud.annotation.get_multi_by_data_product_id(
        db=db, data_product_id=data_product.id, user_id=user.id
    )

    # Assertions
    assert len(annotations) == 2
    annotation_ids = [annotation.id for annotation in annotations]
    created_ids = [annotation.id for annotation in created_annotations]
    for created_id in created_ids:
        assert created_id in annotation_ids


def test_update_annotation(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Original description", geometry_type="Point"
    )

    # Create update data
    update_data = AnnotationUpdate(description="Updated description")

    # Update annotation
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Assertions
    assert updated_annotation.id == annotation.id
    assert updated_annotation.description == "Updated description"
    assert updated_annotation.data_product_id == annotation.data_product_id


def test_update_annotation_with_geometry(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Test annotation", geometry_type="Point"
    )

    # Create new geometry for update
    new_annotation_in = create_annotation_in(
        description="Updated with new geometry", geometry_type="LineString"
    )

    # Create update data with new geometry
    update_data = AnnotationUpdate(
        description=new_annotation_in.description, geom=new_annotation_in.geom
    )

    # Update annotation
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Assertions
    assert updated_annotation.id == annotation.id
    assert updated_annotation.description == "Updated with new geometry"
    assert updated_annotation.geom is not None  # Geometry should be updated


def test_delete_annotation(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Test annotation to delete", geometry_type="Point"
    )
    annotation_id = annotation.id

    # Delete annotation
    deleted_annotation = crud.annotation.remove(db=db, id=annotation_id)

    # Assertions
    assert deleted_annotation is not None
    assert deleted_annotation.id == annotation_id

    # Verify annotation is deleted
    retrieved_annotation = crud.annotation.get(db=db, id=annotation_id)
    assert retrieved_annotation is None


def test_annotation_created_by_id_set_to_null_when_user_deleted(db: Session) -> None:
    # Create a user and data product
    user = create_user(db)
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with user
    annotation = create_annotation(
        db=db,
        description="Test annotation with user",
        geometry_type="Point",
        data_product_id=data_product.id,
        created_by_id=user.id,
    )

    # Verify annotation has user
    assert annotation.created_by_id == user.id

    # Get annotation with created_by relationship loaded to verify user exists
    annotation_with_user = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_user is not None
    assert annotation_with_user.created_by is not None
    assert annotation_with_user.created_by.id == user.id

    # Delete the user
    crud.user.remove(db=db, id=user.id)

    # Refresh annotation from database
    updated_annotation = crud.annotation.get(db=db, id=annotation.id)

    # Assertions - annotation should still exist but created_by_id should be NULL
    assert updated_annotation is not None
    assert updated_annotation.created_by_id is None
    assert updated_annotation.description == "Test annotation with user"

    # Verify created_by relationship is None after user deletion
    updated_annotation_with_user = crud.annotation.get_with_created_by(
        db=db, id=annotation.id
    )
    assert updated_annotation_with_user is not None
    assert updated_annotation_with_user.created_by is None


def test_create_annotation_with_tags(db: Session) -> None:
    """Test creating an annotation with tags in a single operation."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation input with tags
    annotation_in = create_annotation_in(
        description="Annotation with tags",
        geometry_type="Point",
    )
    # Add tags to the input
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["species", "flowering", "drought-resistant"],
    )

    # Create annotation with tags
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    # Assertions
    assert annotation.id is not None
    assert annotation.description == "Annotation with tags"

    # Verify tags were created and associated
    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 3

    tag_names = {tag_row.tag.name for tag_row in annotation_with_tags.tag_rows}
    assert tag_names == {"species", "flowering", "drought-resistant"}


def test_create_annotation_with_duplicate_tags(db: Session) -> None:
    """Test that creating annotation with duplicate tags handles them correctly."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation input with duplicate tags
    annotation_in = create_annotation_in(
        description="Annotation with duplicate tags",
        geometry_type="Point",
    )
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["Species", "species", "SPECIES"],  # Same tag, different cases
    )

    # Create annotation
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    # Verify only one tag was created (tags are normalized to lowercase)
    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 1
    assert annotation_with_tags.tag_rows[0].tag.name == "species"


def test_create_annotation_with_empty_tags_list(db: Session) -> None:
    """Test creating annotation with empty tags list."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    annotation_in = create_annotation_in(
        description="Annotation with no tags",
        geometry_type="Point",
    )
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=[],
    )

    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 0


def test_update_annotation_add_tags(db: Session) -> None:
    """Test adding tags to an existing annotation."""
    # Create annotation without tags
    annotation = create_annotation(
        db=db, description="Original annotation", geometry_type="Point"
    )

    # Verify no tags initially
    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 0

    # Update to add tags
    update_data = AnnotationUpdate(tags=["new-tag-1", "new-tag-2"])
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Verify tags were added
    annotation_with_tags = crud.annotation.get_with_created_by(
        db=db, id=updated_annotation.id
    )
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 2
    tag_names = {tag_row.tag.name for tag_row in annotation_with_tags.tag_rows}
    assert tag_names == {"new-tag-1", "new-tag-2"}


def test_update_annotation_remove_tags(db: Session) -> None:
    """Test removing tags from an annotation."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with tags
    annotation_in = create_annotation_in(
        description="Annotation with tags to remove",
        geometry_type="Point",
    )
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["tag-1", "tag-2", "tag-3"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    # Verify tags were created
    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 3

    # Update to remove all tags
    update_data = AnnotationUpdate(tags=[])
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Verify tags were removed
    annotation_with_tags = crud.annotation.get_with_created_by(
        db=db, id=updated_annotation.id
    )
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 0


def test_update_annotation_modify_tags(db: Session) -> None:
    """Test modifying tags on an annotation (remove some, add others, keep some)."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with initial tags
    annotation_in = create_annotation_in(
        description="Annotation with tags to modify",
        geometry_type="Point",
    )
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["keep", "remove-1", "remove-2"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    # Update tags: keep "keep", remove "remove-1" and "remove-2", add "new-1" and "new-2"
    update_data = AnnotationUpdate(tags=["keep", "new-1", "new-2"])
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Verify correct tags
    annotation_with_tags = crud.annotation.get_with_created_by(
        db=db, id=updated_annotation.id
    )
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 3
    tag_names = {tag_row.tag.name for tag_row in annotation_with_tags.tag_rows}
    assert tag_names == {"keep", "new-1", "new-2"}


def test_update_annotation_tags_reuses_existing_tags(db: Session) -> None:
    """Test that updating annotation reuses existing tags from database."""
    from app.schemas.annotation import AnnotationCreate

    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create a tag that already exists
    existing_tag = create_tag(db, name="existing-tag")
    existing_tag_id = existing_tag.id

    # Create annotation with the existing tag
    annotation_in = create_annotation_in(
        description="Annotation reusing tags",
        geometry_type="Point",
    )
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["existing-tag"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.id,
    )

    # Verify the tag was reused, not created new
    annotation_with_tags = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_tags is not None
    assert len(annotation_with_tags.tag_rows) == 1
    assert annotation_with_tags.tag_rows[0].tag_id == existing_tag_id
    assert annotation_with_tags.tag_rows[0].tag.name == "existing-tag"
