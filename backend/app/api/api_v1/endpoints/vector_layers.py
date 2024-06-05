from typing import Any, Sequence
from uuid import UUID

from geojson_pydantic import FeatureCollection
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("", response_model=FeatureCollection, status_code=status.HTTP_201_CREATED)
def create_vector_layer(
    vector_layer_in: schemas.VectorLayerCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # Raise exception if no features included in feature collection
    if len(vector_layer_in.geojson.features) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GeoJSON Feature Collection must have at least one Feature",
        )
    # Raise exception if features do not have same geometry type
    first_features_geometry_type = vector_layer_in.geojson.features[0].geometry.type
    for feature in vector_layer_in.geojson.features:
        if feature.geometry.type != first_features_geometry_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Features in GeoJSON Feature Collection must have same geometry type",
            )
    features = crud.vector_layer.create_with_project(
        db, obj_in=vector_layer_in, project_id=project.id
    )
    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }
    return FeatureCollection(**feature_collection)


@router.get("/{vector_layer_id}", response_model=FeatureCollection)
def read_vector_layer(
    vector_layer_id: UUID,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # Get layer id for vector layer
    vector_layer = crud.vector_layer.get(db, id=vector_layer_id)
    if not vector_layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector layer not found"
        )
    features = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=vector_layer.layer_id
    )
    if len(features) > 0:
        feature_collection = {
            "type": "FeatureCollection",
            "features": features,
        }
        return feature_collection


@router.get("", response_model=Sequence[FeatureCollection])
def read_vector_layers(
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    feature_collections = crud.vector_layer.get_multi_by_project(
        db, project_id=project.id
    )
    if len(feature_collections) > 0:
        final_feature_collections: list[FeatureCollection] = []
        for features in feature_collections:
            feature_collection = {
                "type": "FeatureCollection",
                "features": features,
            }
            final_feature_collections.append(FeatureCollection(**feature_collection))
        return final_feature_collections
    else:
        return []


@router.delete("/{layer_id}", response_model=FeatureCollection)
def delete_vector_layer(
    layer_id: str,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    removed_vector_layer = crud.vector_layer.remove_layer_by_id(
        db, project_id=project.id, layer_id=layer_id
    )
    if len(removed_vector_layer) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector layer not found"
        )
    return {"type": "FeatureCollection", "features": removed_vector_layer}
