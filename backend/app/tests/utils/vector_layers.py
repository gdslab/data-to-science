from uuid import UUID

from geojson_pydantic import FeatureCollection
from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.project import create_project


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


def get_geojson_feature_collection(
    geom_type: str,
) -> dict[str, str | FeatureCollection]:
    """Creates a GeoJSON feature collection with single feature of
    the provided geometry type.

    Args:
        geom_type (str): Point, LineString, or Polygon.

    Raises:
        ValueError: Raised if unknown geometry type provided.

    Returns:
        Union[Point, LineString, Polygon]: GeoJSON object of requested geometry type.
    """
    if geom_type.lower() == "point":
        return {
            "layer_name": "Point Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        "properties": {
                            "prop0": "value0",
                        },
                    }
                ],
            },
        }
    elif geom_type.lower() == "linestring":
        return {
            "layer_name": "Linestring Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [102.0, 0.0],
                                [103.0, 1.0],
                                [104.0, 0.0],
                                [105.0, 1.0],
                            ],
                        },
                        "properties": {"prop0": "value0", "prop1": 0.0},
                    }
                ],
            },
        }
    elif geom_type.lower() == "polygon":
        return {
            "layer_name": "Polygon Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [100.0, 0.0],
                                    [101.0, 0.0],
                                    [101.0, 1.0],
                                    [100.0, 1.0],
                                    [100.0, 0.0],
                                ],
                            ],
                        },
                        "properties": {
                            "prop0": "value0",
                            "prop1": {
                                "this": "that",
                            },
                        },
                    }
                ],
            },
        }
    elif geom_type.lower() == "multipoint":
        return {
            "layer_name": "Multipoint Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        "properties": {
                            "prop0": "value0",
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [103.0, 1.0],
                        },
                        "properties": {
                            "prop0": "value1",
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [104.0, 1.5],
                        },
                        "properties": {
                            "prop0": "value2",
                        },
                    },
                ],
            },
        }
    else:
        raise ValueError("Unknown geometry type provided")
