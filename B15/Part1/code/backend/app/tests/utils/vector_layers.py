from uuid import UUID

import geopandas as gpd
from geojson_pydantic import FeatureCollection
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.tests.utils.project import create_project
from app.tests.utils.utils import get_geojson_feature_collection


def create_feature_collection(
    db: Session, geom_type: str, project_id: UUID | None = None
) -> schemas.VectorLayerFeatureCollection:
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

    geojson = get_geojson_feature_collection(geom_type)["geojson"]
    fc: FeatureCollection = FeatureCollection(**geojson)
    gdf = gpd.GeoDataFrame.from_features(fc.features, crs="EPSG:4326")

    features = crud.vector_layer.create_with_project(
        db, file_name="test_file.geojson", gdf=gdf, project_id=project_id
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "preview_url": f"{settings.API_DOMAIN}{settings.TEST_STATIC_DIR}"
            f"/projects/{project_id}/vector/{features[0].properties['layer_id']}"
            "/preview.png"
        },
    }

    return schemas.VectorLayerFeatureCollection(**feature_collection)


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

    gdf = gpd.GeoDataFrame.from_features(feature_collection.features, crs="EPSG:4326")

    features = crud.vector_layer.create_with_project(
        db, file_name="test_file.geojson", gdf=gdf, project_id=project_id
    )

    return FeatureCollection(**{"type": "FeatureCollection", "features": features})
