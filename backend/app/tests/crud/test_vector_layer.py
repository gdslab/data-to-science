from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.data_product_metadata import create_metadata
from app.tests.utils.project import create_project
from app.tests.utils.vector_layers import (
    create_feature_collection,
    get_geojson_feature_collection,
)


def test_create_point_vector_layer(db: Session) -> None:
    project = create_project(db)
    fc = get_geojson_feature_collection("Point")
    vector_layer_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=fc["layer_name"], geojson=fc["geojson"]
    )
    point_feature = crud.vector_layer.create_with_project(
        db, obj_in=vector_layer_in, project_id=project.id
    )
    assert point_feature and isinstance(point_feature, list)
    assert len(point_feature) == 1
    assert point_feature[0].properties
    assert point_feature[0].properties.get("layer_name") == fc["layer_name"]


def test_create_linestring_vector_layer(db: Session) -> None:
    project = create_project(db)
    fc = get_geojson_feature_collection("LineString")
    vector_layer_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=fc["layer_name"], geojson=fc["geojson"]
    )
    line_feature = crud.vector_layer.create_with_project(
        db, obj_in=vector_layer_in, project_id=project.id
    )
    assert line_feature and isinstance(line_feature, list)
    assert len(line_feature) == 1
    assert line_feature[0].properties
    assert line_feature[0].properties.get("layer_name") == fc["layer_name"]


def test_create_polygon_vector_layer(db: Session) -> None:
    project = create_project(db)
    fc = get_geojson_feature_collection("Polygon")
    vector_layer_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=fc["layer_name"], geojson=fc["geojson"]
    )
    poly_feature = crud.vector_layer.create_with_project(
        db, obj_in=vector_layer_in, project_id=project.id
    )
    assert poly_feature and isinstance(poly_feature, list)
    assert len(poly_feature) == 1
    assert poly_feature[0].properties
    assert poly_feature[0].properties.get("layer_name") == fc["layer_name"]


def test_create_vector_layer_with_multiple_features(db: Session) -> None:
    project = create_project(db)
    fc = get_geojson_feature_collection("Multipoint")
    vector_layer_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=fc["layer_name"], geojson=fc["geojson"]
    )
    multipoint_features = crud.vector_layer.create_with_project(
        db, obj_in=vector_layer_in, project_id=project.id
    )
    assert multipoint_features and isinstance(multipoint_features, list)
    assert len(multipoint_features) == 3  # Test feature collection has 3 features
    assert (
        multipoint_features[0].properties
        and multipoint_features[1].properties
        and multipoint_features[2].properties
    )
    assert multipoint_features[0].properties.get("layer_name") == fc["layer_name"]
    assert multipoint_features[1].properties.get("layer_name") == fc["layer_name"]
    assert multipoint_features[2].properties.get("layer_name") == fc["layer_name"]
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


def test_read_vector_layers(db: Session) -> None:
    project = create_project(db)
    create_feature_collection(db, "point", project_id=project.id)
    create_feature_collection(db, "linestring", project_id=project.id)
    create_feature_collection(db, "polygon", project_id=project.id)
    create_feature_collection(db, "multipoint", project_id=project.id)

    # list of feature collections (should be four)
    feature_collections = crud.vector_layer.get_multi_by_project(
        db, project_id=project.id
    )
    assert feature_collections and isinstance(feature_collections, list)
    assert len(feature_collections) == 4
    for features in feature_collections:
        assert len(features) > 0
        assert features[0].properties
        if features[0].properties.get("layer_name") != "Multipoint Example":
            assert len(features) == 1  # point, linestring, poly examples have 1 feature
        else:
            assert len(features) == 3  # multipoint example has 3 features
            # check that each feature in the multipoint example has the same layer_id
            layer_id = features[0].properties.get("layer_id")
            for feature in features:
                assert feature.properties
                assert feature.properties.get("layer_id") == layer_id


def test_remove_vector_layer(db: Session) -> None:
    project = create_project(db)
    # point feature collection with three points (features)
    multi_feature = create_feature_collection(db, "multipoint", project_id=project.id)
    multi_feature_layer_id = multi_feature.features[0].properties["layer_id"]
    multi_feature_removed = crud.vector_layer.remove_layer_by_id(
        db, project_id=project.id, layer_id=multi_feature_layer_id
    )
    multi_feature_after_removed = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=multi_feature_layer_id
    )
    assert isinstance(multi_feature_after_removed, list)
    assert len(multi_feature_after_removed) == 0
    assert multi_feature_removed
    assert multi_feature_removed == multi_feature.features


def test_remove_vector_layer_removes_metadata_associated_with_layer(
    db: Session,
) -> None:
    project = create_project(db)
    metadata = create_metadata(db, project_id=project.id)
    # get metadata associated with vector layer id and data product id
    metadata_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata.data_product_id,
        vector_layer_id=metadata.vector_layer_id,
    )
    assert (
        metadata_in_db and isinstance(metadata_in_db, list) and len(metadata_in_db) > 0
    )
    # create metadata for a different vector layer and data product
    metadata_other = create_metadata(db, project_id=project.id)
    # get metadata associated with vector layer id and data product id
    metadata_other_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata_other.data_product_id,
        vector_layer_id=metadata_other.vector_layer_id,
    )
    # confirm vector layer in database
    vector_layer = crud.vector_layer.get(db, id=metadata.vector_layer_id)
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
        data_product_id=metadata.data_product_id,
        vector_layer_id=metadata.vector_layer_id,
    )
    assert not metadata_after_remove
    # confirm other metadata not associated with the vector id remains
    metadata_other_after_remove = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata_other.data_product_id,
        vector_layer_id=metadata_other.vector_layer_id,
    )
    assert (
        isinstance(metadata_other_after_remove, list)
        and len(metadata_other_after_remove) == 1
    )
