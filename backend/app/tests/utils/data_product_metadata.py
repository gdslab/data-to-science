import json
import os
from typing import TypedDict
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from geojson_pydantic import Feature, FeatureCollection
from sqlalchemy.orm import Session

from app import crud
from app.models.data_product_metadata import DataProductMetadata
from app.schemas.data_product_metadata import DataProductMetadataCreate, ZonalStatistics
from app.tasks import generate_zonal_statistics
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.vector_layers import (
    create_vector_layer_with_provided_feature_collection,
)


def get_zonal_statistics(
    in_raster: str, bbox_feature: Feature
) -> list[ZonalStatistics]:
    """Returns zonal statistics for polygon overlaying a single-band raster.

    Args:
        in_raster (str): Path to single-band raster.
        bbox_feature (str): GeoJSON Feature for polygon.

    Returns:
        list[ZonalStats]: List of zonal statistic dictionaries for each zone.
    """
    bbox_json_string = json.dumps(jsonable_encoder(bbox_feature.__dict__))
    stats = generate_zonal_statistics(in_raster, bbox_json_string)

    return stats


def get_zonal_statistics_bulk(
    in_raster: str, feature_collection: FeatureCollection
) -> list[ZonalStatistics]:
    """Returns zonal statistics for multiple polygons in a Feature Collection
    overlaying a single-band raster.

    Args:
        in_raster (str): Path to single-band raster.
        feature_collection (FeatureCollection): GeoJSON FeatureCollection for zones.

    Returns:
        list[ZonalStatistics]: List of zonal statistic dictionaries for each zone.
    """

    feature_collection_string = json.dumps(
        jsonable_encoder(feature_collection.__dict__)
    )
    stats = generate_zonal_statistics(in_raster, feature_collection_string)

    return stats


def create_metadata(
    db: Session,
    data_product_id: UUID | None = None,
    vector_layer_id: UUID | None = None,
) -> DataProductMetadata:
    """Create DataProductMetadata record with zonal statistics.

    Args:
        db (Session): Database session.

    Returns:
        DataProductMetadata: Instance of DataProductMetadata.
    """
    if not data_product_id:
        data_product = SampleDataProduct(db, data_type="ortho")
        data_product = data_product.obj
    else:
        data_product = crud.data_product.get(db, id=data_product_id)

    bbox_filepath = os.path.join(
        os.sep, "app", "app", "tests", "data", "test_bbox.geojson"
    )
    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    bbox_feature = bbox_feature_collection.features[0]
    project = create_project(db)
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )

    if not vector_layer_id:
        vector_layer_id = bbox_vector_layer.features[0].properties["id"]

    stats = get_zonal_statistics(data_product.filepath, bbox_feature)
    metadata_in = DataProductMetadataCreate(
        category="zonal",
        properties={"stats": stats[0]},
        vector_layer_id=vector_layer_id,
    )
    metadata = crud.data_product_metadata.create_with_data_product(
        db, obj_in=metadata_in, data_product_id=data_product.id
    )
    return metadata
