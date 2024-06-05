import json
from collections import defaultdict
from uuid import UUID
from typing import List

from geojson_pydantic import Feature
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.vector_layer import VectorLayer
from app.schemas.vector_layer import VectorLayerCreate, VectorLayerUpdate
from app.utils.unique_id import generate_unique_id


class CRUDVectorLayer(CRUDBase[VectorLayer, VectorLayerCreate, VectorLayerUpdate]):
    def create_with_project(
        self, db: Session, obj_in: VectorLayerCreate, project_id: UUID
    ) -> List[Feature]:
        """Creates new vector layer records for features in a feature collection.

        Args:
            db (Session): Database session.
            obj_in (VectorLayerCreate): Feature name and GeoJSON for new vector data.
            project_id (UUID): ID of project the vector data belongs to.

        Returns:
            List[Feature]: List of GeoJSON features.
        """
        # List of features from feature collection
        features = obj_in.geojson.features
        # Unique ID for feature collection
        layer_id = generate_unique_id()
        # List of vector layer objects
        vector_layers = []
        # Create record in database for each feature
        for feature in features:
            geometry = feature.geometry.__dict__
            properties = jsonable_encoder(feature.properties)
            # Serialize geometry for ST_GeomFromGeoJSON function
            geom = func.ST_GeomFromGeoJSON(json.dumps(geometry))
            # Layer ID will be same for each feature from the feature collection
            vector_layer = VectorLayer(
                layer_name=obj_in.layer_name,
                layer_id=layer_id,
                geom=geom,
                properties=properties,
                project_id=project_id,
            )
            # Add vector layer object to list
            vector_layers.append(vector_layer)

        # Add and commit all vector layers
        with db as session:
            session.add_all(vector_layers)
            session.commit()

        return self.get_vector_layer_by_id(db, project_id=project_id, layer_id=layer_id)

    def get_vector_layer_by_id(
        self, db: Session, project_id: UUID, layer_id: str
    ) -> List[Feature]:
        """Fetches vector layers from feature collection associated with layer ID.

        Args:
            db (Session): Database session.
            project_id (UUID): Project ID for feature collection.
            layer_id (str): Layer ID for feature collection.

        Returns:
            List[Feature]: List of GeoJSON features.
        """
        statement = select(func.ST_AsGeoJSON(VectorLayer)).where(
            and_(
                VectorLayer.layer_id == layer_id,
                VectorLayer.project_id == project_id,
                VectorLayer.is_active,
            )
        )
        with db as session:
            vector_layers = session.scalars(statement).all()
            # Deserialize features and create Feature objects for each feature
            return [Feature(**json.loads(feature)) for feature in vector_layers]

    def get_multi_by_project(
        self, db: Session, project_id: UUID
    ) -> List[List[Feature]]:
        """Fetches all vector layers and groups by feature collections.

        Args:
            db (Session): Database session.
            project_id (UUID): Vector layer's project ID.

        Returns:
            List[List[Feature]]: Features in Feature Collections.
        """
        # Assign new keys empty list
        vector_layers = defaultdict(list)
        with db as session:
            for feature in (
                session.query(func.ST_AsGeoJSON(VectorLayer))
                .order_by(VectorLayer.id)
                .where(
                    and_(VectorLayer.project_id == project_id, VectorLayer.is_active)
                )
            ):
                feature = Feature(**json.loads(feature[0]))
                vector_layers[feature.properties["layer_id"]].append(feature)

        # Each list element is a list of features from a feature collection
        return list(vector_layers.values())

    def remove_layer_by_id(
        self, db: Session, project_id: UUID, layer_id: str
    ) -> List[Feature]:
        """_summary_

        Args:
            db (Session): Database session.
            project_id (UUID): Project ID.
            layer_id (str): Layer ID for feature collection.

        Returns:
            List[Feature]: List of GeoJSON features that were removed.
        """
        # Find all features associated with the layer feature collection
        features_to_remove = self.get_vector_layer_by_id(
            db, project_id=project_id, layer_id=layer_id
        )
        removed_features = []
        if len(features_to_remove) > 0:
            for feature in features_to_remove:
                # Unique UUID associated with the feature
                if feature.properties and "id" in feature.properties:
                    feature_uuid = feature.properties["id"]
                    # Remove feature using feature's UUID
                    self.remove(db, id=feature_uuid)
                    removed_features.append(feature)

        return removed_features


vector_layer = CRUDVectorLayer(VectorLayer)
