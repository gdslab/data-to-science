from sqlalchemy.orm import Session

from app import crud, schemas
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
    assert point_feature[0].properties["layer_name"] == fc["layer_name"]


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
    assert line_feature[0].properties["layer_name"] == fc["layer_name"]


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
    assert poly_feature[0].properties["layer_name"] == fc["layer_name"]


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
    assert multipoint_features[0].properties["layer_name"] == fc["layer_name"]
    assert multipoint_features[1].properties["layer_name"] == fc["layer_name"]
    assert multipoint_features[2].properties["layer_name"] == fc["layer_name"]
    # unique layer id assigned to feature collection on creation
    layer_id = multipoint_features[0].properties["layer_id"]
    assert multipoint_features[1].properties["layer_id"] == layer_id
    assert multipoint_features[2].properties["layer_id"] == layer_id


def test_read_vector_layer(db: Session) -> None:
    point_fc = create_feature_collection(db, "point")
    point_features = crud.vector_layer.get_vector_layer_by_id(
        db,
        project_id=point_fc.features[0].properties["project_id"],
        layer_id=point_fc.features[0].properties["layer_id"],
    )
    assert point_features and isinstance(point_features, list)
    assert len(point_features) == 1
    assert point_fc.features[0].properties["id"] == point_features[0].properties["id"]
    assert (
        point_fc.features[0].properties["layer_name"]
        == point_features[0].properties["layer_name"]
    )
    assert (
        point_fc.features[0].properties["properties"]
        == point_features[0].properties["properties"]
    )


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
        if features[0].properties["layer_name"] != "Multipoint Example":
            assert len(features) == 1  # point, linestring, poly examples have 1 feature
        else:
            assert len(features) == 3  # multipoint example has 3 features
            # check that each feature in the multipoint example has the same layer_id
            layer_id = features[0].properties["layer_id"]
            for feature in features:
                assert feature.properties["layer_id"] == layer_id
