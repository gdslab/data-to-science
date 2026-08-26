from uuid import UUID

from geojson_pydantic import Feature
from sqlalchemy.orm import Session

from app import crud
from app.models.annotation import Annotation
from app.models.enums.visibility import Visibility
from app.schemas.annotation import AnnotationCreate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.utils import get_geojson_feature_collection


def create_annotation(
    db: Session,
    description: str = "Test annotation",
    geometry_type: str = "Point",
    data_product_id: UUID | None = None,
    created_by_id: UUID | None = None,
    visibility: Visibility = Visibility.OWNER,
) -> Annotation:
    """Create a test annotation.

    Args:
        db (Session): Database session.
        description (str): Annotation description.
        geometry_type (str): Type of geometry ("Point", "LineString", "Polygon").
        data_product_id (UUID | None): Data product ID. If None, creates a new data product.
        created_by_id (UUID | None): User ID who created the annotation.
        visibility (Visibility): Annotation visibility level.

    Returns:
        Annotation: Created annotation object.
    """
    # Create data product if not provided
    if data_product_id is None:
        sample_data_product = SampleDataProduct(db)
        data_product_id = sample_data_product.obj.id

    # Create GeoJSON Feature
    vector_layer_dict = get_geojson_feature_collection(geometry_type)
    sample_feature: Feature = Feature(**vector_layer_dict["geojson"]["features"][0])

    # Create annotation
    annotation_in = AnnotationCreate(
        description=description,
        geom=sample_feature,
        visibility=visibility,
    )

    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_in,
        data_product_id=data_product_id,
        created_by_id=created_by_id,
    )

    return annotation


def create_annotation_in(
    description: str = "Test annotation", geometry_type: str = "Point"
) -> AnnotationCreate:
    """Create an AnnotationCreate schema for testing.

    Args:
        description (str): Annotation description.
        geometry_type (str): Type of geometry ("Point", "LineString", "Polygon").

    Returns:
        AnnotationCreate: Annotation creation schema.
    """
    # Create GeoJSON Feature
    vector_layer_dict = get_geojson_feature_collection(geometry_type)
    sample_feature: Feature = Feature(**vector_layer_dict["geojson"]["features"][0])

    return AnnotationCreate(
        description=description,
        geom=sample_feature,
    )


def create_multiple_annotations(
    db: Session,
    count: int = 3,
    data_product_id: UUID | None = None,
    base_description: str = "Test annotation",
    created_by_id: UUID | None = None,
    visibility: Visibility = Visibility.OWNER,
) -> list[Annotation]:
    """Create multiple test annotations for the same data product.

    Args:
        db (Session): Database session.
        count (int): Number of annotations to create.
        data_product_id (UUID | None): Data product ID. If None, creates a new data product.
        base_description (str): Base description for annotations (will be numbered).
        created_by_id (UUID | None): User ID who created the annotations.
        visibility (Visibility): Annotation visibility level.

    Returns:
        list[Annotation]: List of created annotation objects.
    """
    # Create data product if not provided
    if data_product_id is None:
        sample_data_product = SampleDataProduct(db)
        data_product_id = sample_data_product.obj.id

    annotations = []
    geometry_types = ["Point", "LineString", "Polygon"]

    for i in range(count):
        geometry_type = geometry_types[i % len(geometry_types)]
        description = f"{base_description} {i + 1}"

        annotation = create_annotation(
            db=db,
            description=description,
            geometry_type=geometry_type,
            data_product_id=data_product_id,
            created_by_id=created_by_id,
            visibility=visibility,
        )
        annotations.append(annotation)

    return annotations
