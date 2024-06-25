import os

from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.utils import create_vector_layer_preview
from app.tests.utils.project import create_project
from app.tests.utils.vector_layers import get_geojson_feature_collection


def test_create_vector_layer_preview_image(
    db: Session, normal_user_access_token: str
) -> None:
    # project
    project = create_project(db)
    # point preview
    point_fc = get_geojson_feature_collection("point")
    point_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=point_fc["layer_name"], geojson=point_fc["geojson"]
    )
    point_features = crud.vector_layer.create_with_project(
        db, obj_in=point_in, project_id=project.id
    )
    point_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=point_features[0].properties["layer_id"],
        features=point_features,
    )
    # line preview
    line_fc = get_geojson_feature_collection("linestring")
    line_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=line_fc["layer_name"], geojson=line_fc["geojson"]
    )
    line_features = crud.vector_layer.create_with_project(
        db, obj_in=line_in, project_id=project.id
    )
    line_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=line_features[0].properties["layer_id"],
        features=line_features,
    )
    # polygon preview
    polygon_fc = get_geojson_feature_collection("polygon")
    polygon_in = schemas.vector_layer.VectorLayerCreate(
        layer_name=polygon_fc["layer_name"], geojson=polygon_fc["geojson"]
    )
    polygon_features = crud.vector_layer.create_with_project(
        db, obj_in=polygon_in, project_id=project.id
    )
    polygon_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=polygon_features[0].properties["layer_id"],
        features=polygon_features,
    )

    assert os.path.exists(point_preview)
    assert os.path.exists(line_preview)
    assert os.path.exists(polygon_preview)
