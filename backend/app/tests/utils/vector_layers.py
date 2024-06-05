from uuid import UUID

from geojson_pydantic import FeatureCollection
from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.project import create_project
from app.tests.utils.utils import get_geojson_feature_collection


def create_feature_collection(
    db: Session, geom_type: str, project_id: UUID | None = None
) -> FeatureCollection:
    """Creates GeoJSON feature collection with feature of specified geometry type.

    Args:
        db (Session): Database session.
        geom_type (str): Point, LineString, or Polygon.

    Returns:
        FeatureCollection: GeoJSON feature collection with feature.
    """
    if not project_id:
        project = create_project(db)
        project_id = project.id
    feature = get_geojson_feature_collection(geom_type)
    vector_layer_in = schemas.VectorLayerCreate(
        layer_name=feature["layer_name"], geojson=feature["geojson"]
    )
    features = crud.vector_layer.create_with_project(
        db, vector_layer_in, project_id=project_id
    )
    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }
    return FeatureCollection(**feature_collection)


def create_vector_layer_with_provided_feature_collection(
    db: Session, feature_collection: FeatureCollection, project_id: UUID | None = None
) -> FeatureCollection:
    """Create new vector layer with provided feature collection.

    Args:
        db (Session): Database session.
        feature_collection (FeatureCollection): GeoJSON Feature Collection.
        project_id (UUID | None, optional): Project ID. Defaults to None.

    Returns:
        FeatureCollection: GeoJSON Feature Collection for vector layer.
    """
    if not project_id:
        project = create_project(db)
        project_id = project.id
    vector_layer_in = schemas.VectorLayerCreate(
        layer_name="Feature Collection Example", geojson=feature_collection.__dict__
    )
    features = crud.vector_layer.create_with_project(
        db, vector_layer_in, project_id=project_id
    )
    feature_collection = {"type": "FeatureCollection", "features": features}
    return FeatureCollection(**feature_collection)
