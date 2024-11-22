import os
from typing import Any, Dict

import geopandas as gpd
from geojson_pydantic import FeatureCollection
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_metadata import (
    create_zonal_metadata,
    get_zonal_feature_collection,
)
from app.tests.utils.project import create_project
from app.tests.utils.utils import VectorLayerDict
from app.tests.utils.vector_layers import (
    create_feature_collection,
    create_vector_layer_with_provided_feature_collection,
    get_geojson_feature_collection,
)


def test_create_point_vector_layer(db: Session) -> None:
    project = create_project(db)
    vector_layer: VectorLayerDict = get_geojson_feature_collection("Point")
    gdf = gpd.GeoDataFrame.from_features(
        vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    point_feature = crud.vector_layer.create_with_project(
        db, file_name=vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    assert point_feature and isinstance(point_feature, list)
    assert len(point_feature) == 1
    assert point_feature[0].properties
    assert point_feature[0].properties.get("layer_name") == vector_layer["layer_name"]


def test_create_linestring_vector_layer(db: Session) -> None:
    project = create_project(db)
    vector_layer: VectorLayerDict = get_geojson_feature_collection("LineString")
    gdf = gpd.GeoDataFrame.from_features(
        vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    line_feature = crud.vector_layer.create_with_project(
        db, file_name=vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    assert line_feature and isinstance(line_feature, list)
    assert len(line_feature) == 1
    assert line_feature[0].properties
    assert line_feature[0].properties.get("layer_name") == vector_layer["layer_name"]


def test_create_polygon_vector_layer(db: Session) -> None:
    project = create_project(db)
    vector_layer: VectorLayerDict = get_geojson_feature_collection("Polygon")
    gdf = gpd.GeoDataFrame.from_features(
        vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    poly_feature = crud.vector_layer.create_with_project(
        db, file_name=vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    assert poly_feature and isinstance(poly_feature, list)
    assert len(poly_feature) == 1
    assert poly_feature[0].properties
    assert poly_feature[0].properties.get("layer_name") == vector_layer["layer_name"]


def test_create_vector_layer_with_multiple_features(db: Session) -> None:
    project = create_project(db)
    vector_layer: VectorLayerDict = get_geojson_feature_collection("Multipoint")
    gdf = gpd.GeoDataFrame.from_features(
        vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    multipoint_features = crud.vector_layer.create_with_project(
        db, file_name=vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    assert multipoint_features and isinstance(multipoint_features, list)
    assert len(multipoint_features) == 3  # Test feature collection has 3 features
    assert (
        multipoint_features[0].properties
        and multipoint_features[1].properties
        and multipoint_features[2].properties
    )
    assert (
        multipoint_features[0].properties.get("layer_name")
        == vector_layer["layer_name"]
    )
    assert (
        multipoint_features[1].properties.get("layer_name")
        == vector_layer["layer_name"]
    )
    assert (
        multipoint_features[2].properties.get("layer_name")
        == vector_layer["layer_name"]
    )
    # unique layer id assigned to feature collection on creation
    layer_id = multipoint_features[0].properties.get("layer_id")
    assert multipoint_features[1].properties.get("layer_id") == layer_id
    assert multipoint_features[2].properties.get("layer_id") == layer_id


def test_read_vector_layer(db: Session) -> None:
    point_fc = create_feature_collection(db, "point")
    point_features = crud.vector_layer.get_vector_layer_by_id(
        db,
        project_id=point_fc.features[0].properties["project_id"],
        layer_id=point_fc.features[0].properties["layer_id"],
    )
    assert point_features and isinstance(point_features, list)
    assert len(point_features) == 1
    assert point_fc.features[0].properties and point_features[0].properties
    assert point_fc.features[0].properties.get("id") == point_features[
        0
    ].properties.get("id")
    assert point_fc.features[0].properties.get("layer_name") == point_features[
        0
    ].properties.get("layer_name")
    assert point_fc.features[0].properties.get("properties") == point_features[
        0
    ].properties.get("properties")
    project_id = point_fc.features[0].properties["project_id"]
    layer_id = point_fc.features[0].properties["layer_id"]
    assert os.path.exists(
        f"{settings.TEST_STATIC_DIR}/projects/{project_id}/vector/{layer_id}/preview.png"
    )


def test_read_vector_layers(db: Session) -> None:
    project = create_project(db)
    create_feature_collection(db, "point", project_id=project.id)
    create_feature_collection(db, "linestring", project_id=project.id)
    create_feature_collection(db, "polygon", project_id=project.id)
    create_feature_collection(db, "multipoint", project_id=project.id)

    # list of feature collections (should be four)
    vector_layers = crud.vector_layer.get_multi_by_project(db, project_id=project.id)
    assert vector_layers and isinstance(vector_layers, list)
    assert len(vector_layers) == 4
    for layer in vector_layers:
        assert isinstance(layer, tuple)
        assert isinstance(layer[0], str)
        assert layer[1] == "test_file.geojson"
        assert layer[2] in ["point", "line", "polygon"]


def test_read_vector_layer_by_id_with_metadata(db: Session) -> None:
    # create a project with a single band data product and vector layer
    project = create_project(db)
    data_product = SampleDataProduct(db, data_type="dsm", project=project)
    feature_collection = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=get_zonal_feature_collection(), project_id=project.id
    )
    # generate zonal statistics metadata using data product and vector layer
    for feature in feature_collection.features:
        vector_layer_id = feature.properties["id"]
        create_zonal_metadata(
            db,
            data_product_id=data_product.obj.id,
            project_id=project.id,
            vector_layer_id=vector_layer_id,
        )
    # get layer_id from first feature
    layer_id = feature_collection.features[0].properties["layer_id"]
    # retrieve vector layers as features with zonal metadata in properties
    vector_layers_with_zonal_metadata = (
        crud.vector_layer.get_vector_layer_by_id_with_metadata(
            db,
            project_id=project.id,
            data_product_id=data_product.obj.id,
            layer_id=layer_id,
            metadata_category="zonal",
        )
    )
    assert vector_layers_with_zonal_metadata
    assert isinstance(vector_layers_with_zonal_metadata, list)
    assert len(vector_layers_with_zonal_metadata) == len(feature_collection.features)
    # confirm first feature has expected zonal statistics in its properties
    expected_zonal_stats = ["min", "max", "mean", "median", "std", "count"]
    for expected_zonal_stat in expected_zonal_stats:
        assert expected_zonal_stat in vector_layers_with_zonal_metadata[0].properties


def test_remove_vector_layer(db: Session) -> None:
    project = create_project(db)
    # point feature collection with three points (features)
    multi_feature = create_feature_collection(db, "multipoint", project_id=project.id)
    multi_feature_layer_id = multi_feature.features[0].properties["layer_id"]
    crud.vector_layer.remove_layer_by_id(
        db, project_id=project.id, layer_id=multi_feature_layer_id
    )
    multi_feature_after_removed = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=multi_feature_layer_id
    )
    assert isinstance(multi_feature_after_removed, list)
    assert len(multi_feature_after_removed) == 0


def test_remove_vector_layer_removes_metadata_associated_with_layer(
    db: Session,
) -> None:
    project = create_project(db)
    metadata = create_zonal_metadata(db, project_id=project.id)[0]
    # get metadata associated with vector layer id and data product id
    metadata_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata[0].data_product_id,
        vector_layer_id=metadata[0].vector_layer_id,
    )
    assert (
        metadata_in_db and isinstance(metadata_in_db, list) and len(metadata_in_db) > 0
    )
    # create metadata for a different vector layer and data product
    metadata_other = create_zonal_metadata(db, project_id=project.id)[0]
    # get metadata associated with vector layer id and data product id
    metadata_other_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata_other[0].data_product_id,
        vector_layer_id=metadata_other[0].vector_layer_id,
    )
    # confirm vector layer in database
    vector_layer = crud.vector_layer.get(db, id=metadata[0].vector_layer_id)
    assert vector_layer
    # remove vector layer from db
    crud.vector_layer.remove_layer_by_id(
        db, project_id=project.id, layer_id=vector_layer.layer_id
    )
    # confirm vector layer removed from db
    vector_layer_after_remove = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=vector_layer.layer_id
    )
    assert (
        isinstance(vector_layer_after_remove, list)
        and len(vector_layer_after_remove) == 0
    )
    # confirm metadata also removed from db
    metadata_after_remove = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata[0].data_product_id,
        vector_layer_id=metadata[0].vector_layer_id,
    )
    assert not metadata_after_remove
    # confirm other metadata not associated with the vector id remains
    metadata_other_after_remove = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata_other[0].data_product_id,
        vector_layer_id=metadata_other[0].vector_layer_id,
    )
    assert (
        isinstance(metadata_other_after_remove, list)
        and len(metadata_other_after_remove) == 1
    )
