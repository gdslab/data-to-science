import json
import os
from typing import Dict, List, Tuple, TypedDict, Union
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
    stats = generate_zonal_statistics(in_raster, feature_collection.__dict__)

    return stats


def get_zonal_feature_collection(
    single_feature: bool = False,
) -> Union[FeatureCollection, Feature]:
    """Returns either single Feature or FeatureCollection for polygon(s) inside the
    test.tif single-band dataset.

    Args:
        single_feature (bool, optional): Return single Feature if True. Defaults to False.

    Returns:
        Union[FeatureCollection, Feature]: FeatureCollection of zones or single Feature.
    """
    zones_filepath = os.path.join(
        os.sep,
        "app",
        "app",
        "tests",
        "data",
        "zones_inside_test_tif.geojson",
    )
    with open(zones_filepath) as zones_file:
        # create vector layer record for bbox
        zones_feature_collection_dict = json.loads(zones_file.read())

    zones_feature_collection = FeatureCollection(**zones_feature_collection_dict)
    if single_feature:
        return zones_feature_collection.features[0]
    else:
        return zones_feature_collection


def create_metadata(
    db: Session,
    data_product_id: UUID | None = None,
    vector_layer_id: UUID | None = None,
    project_id: UUID | None = None,
    single_feature: bool = False,
    no_props: bool = False,
) -> Tuple[List[DataProductMetadata], str, Dict]:
    """Create DataProductMetadata record with zonal statistics.

    Args:
        db (Session): Database session.
        data_product_id (UUID | None, optional): Data product ID. Defaults to None.
        vector_layer_id (UUID | None, optional): Vector layer ID. Defaults to None.
        project_id (UUID | None, optional): Project ID. Defaults to None.

    Returns:
        Tuple[List[DataProductMetadata], str, Dict]: Instance of DataProductMetadata and layer_id.
    """
    if not project_id:
        project = create_project(db)
    else:
        project = crud.project.get(db, id=project_id)
    if not data_product_id:
        data_product = SampleDataProduct(db, data_type="dsm", project=project)
        data_product = data_product.obj
    else:
        data_product = crud.data_product.get(db, id=data_product_id)

    if not single_feature:
        if not no_props:
            bbox_filepath = os.path.join(
                os.sep, "app", "app", "tests", "data", "zones_inside_test_tif.geojson"
            )
        else:
            bbox_filepath = os.path.join(
                os.sep,
                "app",
                "app",
                "tests",
                "data",
                "zones_inside_test_tif_no_props.geojson",
            )
    else:
        bbox_filepath = os.path.join(
            os.sep, "app", "app", "tests", "data", "test_bbox.geojson"
        )

    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    bbox_feature = bbox_feature_collection.features[0]
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )

    all_zonal_stats = get_zonal_statistics(
        data_product.filepath, bbox_feature_collection
    )
    all_metadata = []
    original_props = bbox_vector_layer.features[0].properties["properties"]

    for index, feature in enumerate(bbox_vector_layer.features):
        if not vector_layer_id:
            vid = feature.properties["id"]
        else:
            vid = vector_layer_id
        zonal_stats = all_zonal_stats[index]
        metadata_in = DataProductMetadataCreate(
            category="zonal",
            properties={"geojson": zonal_stats},
            vector_layer_id=vid,
        )
        metadata = crud.data_product_metadata.create_with_data_product(
            db, obj_in=metadata_in, data_product_id=data_product.id
        )
        all_metadata.append(metadata)

    return (
        all_metadata,
        bbox_vector_layer.features[0].properties["layer_id"],
        original_props,
    )
