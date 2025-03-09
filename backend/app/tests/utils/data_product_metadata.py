import json
import os
from typing import Dict, List, Tuple, TypedDict, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from geojson_pydantic import Feature, FeatureCollection
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app import crud
from app.models.data_product_metadata import DataProductMetadata
from app.models.vector_layer import VectorLayer
from app.schemas.data_product_metadata import DataProductMetadataCreate, ZonalStatistics
from app.tasks.toolbox_tasks import calculate_zonal_statistics
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.vector_layers import (
    create_vector_layer_with_provided_feature_collection,
)


def get_zonal_statistics(
    in_raster: str, feature_collection: FeatureCollection
) -> List[ZonalStatistics]:
    """Returns zonal statistics for multiple polygons in a Feature Collection
    overlaying a single-band raster.

    Args:
        in_raster (str): Path to single-band raster.
        feature_collection (FeatureCollection): GeoJSON FeatureCollection for zones.

    Returns:
        list[ZonalStatistics]: List of zonal statistic dictionaries for each zone.
    """
    stats = calculate_zonal_statistics(in_raster, feature_collection.__dict__)

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


def create_zonal_metadata(
    db: Session,
    data_product_id: UUID | None = None,
    vector_layer_feature_id: UUID | None = None,
    project_id: UUID | None = None,
    single_feature: bool = False,
    no_props: bool = False,
) -> Tuple[List[DataProductMetadata], str, Dict]:
    """Create DataProductMetadata record with zonal statistics.

    Args:
        db (Session): Database session.
        data_product_id (UUID | None, optional): Data product ID. Defaults to None.
        vector_layer_feature_id (UUID | None, optional): Vector layer ID. Defaults to None.
        project_id (UUID | None, optional): Project ID. Defaults to None.

    Returns:
        Tuple[List[DataProductMetadata], str, Dict]: Instance of DataProductMetadata and layer_id.
    """
    # create project if one is not provided
    if not project_id:
        project = create_project(db)
    else:
        project_in_db = crud.project.get(db, id=project_id)
        if not project_in_db:
            raise Exception("Cannot find test project in db")
        project = project_in_db
    # create data product if ID for one is not provided
    if not data_product_id:
        samp_data_product = SampleDataProduct(db, data_type="dsm", project=project)
        data_product = samp_data_product.obj
    else:
        data_product_in_db = crud.data_product.get(db, id=data_product_id)
        if not data_product_in_db:
            raise Exception("Cannot find test data product in db")
        data_product = data_product_in_db
    # if vector layer is not provided, create vector layers from test data
    if not vector_layer_feature_id:
        test_data_dir = os.path.join(os.sep, "app", "app", "tests", "data")
        if not no_props:
            zones_test_data_filepath = os.path.join(
                test_data_dir,
                "zones_inside_test_tif.geojson",
            )
        else:
            # empty properties attribute for geojson features
            zones_test_data_filepath = os.path.join(
                test_data_dir,
                "zones_inside_test_tif_no_props.geojson",
            )

        with open(zones_test_data_filepath) as zones_file:
            # create vector layer record for bbox
            zones_geojson_dict = json.loads(zones_file.read())

        # create feature collection from geojson data
        zones_feature_collection: FeatureCollection = FeatureCollection(
            **zones_geojson_dict
        )
        # create vector layer records for each zone feature
        vector_layers_feature_collection = (
            create_vector_layer_with_provided_feature_collection(
                db, feature_collection=zones_feature_collection, project_id=project.id
            )
        )
    else:
        # query vector layer using vector layer id and project id
        statement = select(func.ST_AsGeoJSON(VectorLayer)).where(
            and_(
                VectorLayer.feature_id == vector_layer_feature_id,
                VectorLayer.project_id == project_id,
            )
        )
        with db as session:
            # existing vector layer in database as geojson feature string
            vector_layer = session.execute(statement).scalar_one_or_none()
            assert vector_layer
            # create feature collection for vector layer
            vector_layers_feature_collection = FeatureCollection(
                **{
                    "type": "FeatureCollection",
                    "features": [Feature(**json.loads(vector_layer))],
                }
            )

    # fetch zonal statistics for data product and zonal feature collection
    all_zonal_stats = get_zonal_statistics(
        data_product.filepath, vector_layers_feature_collection
    )
    all_metadata = []
    # get original properties from first feature
    original_props = vector_layers_feature_collection.features[0].properties.get(
        "properties"
    )

    # only include first zone feature if single feature is True
    if single_feature:
        zone_features = [vector_layers_feature_collection.features[0]]
    else:
        zone_features = vector_layers_feature_collection.features

    # iterate over each zone feature
    for index, feature in enumerate(zone_features):
        if not vector_layer_feature_id:
            vid = feature.properties["feature_id"]
        else:
            vid = vector_layer_feature_id
        # create data product metadata record for current feature and zone stats
        zonal_stats = all_zonal_stats[index]
        metadata_in = DataProductMetadataCreate(
            category="zonal",
            properties={"stats": zonal_stats},
            vector_layer_feature_id=vid,
        )
        metadata = crud.data_product_metadata.create_with_data_product(
            db, obj_in=metadata_in, data_product_id=data_product.id
        )
        all_metadata.append(metadata)

    return (
        all_metadata,
        vector_layers_feature_collection.features[0].properties["layer_id"],
        original_props,
    )
