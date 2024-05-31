import json
import os
from typing import TypedDict

from fastapi.encoders import jsonable_encoder
from geojson_pydantic import FeatureCollection
from sqlalchemy.orm import Session

from app import crud
from app.models.data_product_metadata import DataProductMetadata
from app.schemas.data_product_metadata import DataProductMetadataCreate, ZonalStatistics
from app.tasks import generate_zonal_statistics
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project


def get_zonal_statistics(in_raster: str, bbox_feature: str) -> list[ZonalStatistics]:
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


def create_metadata(db: Session) -> DataProductMetadata:
    """Create DataProductMetadata record with zonal statistics.

    Args:
        db (Session): Database session.

    Returns:
        DataProductMetadata: Instance of DataProductMetadata.
    """
    data_product = SampleDataProduct(db, data_type="ortho")
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
    stats = get_zonal_statistics(data_product.obj.filepath, bbox_feature)
    metadata_in = DataProductMetadataCreate(
        category="zonal",
        properties={"stats": stats[0]},
        vector_layer_id=bbox_vector_layer.features[0].properties["id"],
    )
    metadata = crud.data_product_metadata.create_with_data_product(
        db, obj_in=metadata_in, data_product_id=data_product.obj.id
    )
    return metadata
