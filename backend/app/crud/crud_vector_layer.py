import json
from collections import defaultdict
from uuid import UUID
from typing import List, Tuple

import geopandas as gpd
from geojson_pydantic import Feature
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, delete, func, select, text, update
from sqlalchemy.orm import Session

from app import crud
from app.api.utils import create_vector_layer_preview
from app.crud.base import CRUDBase
from app.models.data_product_metadata import DataProductMetadata
from app.models.vector_layer import VectorLayer
from app.schemas.vector_layer import VectorLayerCreate, VectorLayerUpdate
from app.utils.unique_id import generate_unique_id


class CRUDVectorLayer(CRUDBase[VectorLayer, VectorLayerCreate, VectorLayerUpdate]):
    def create_with_project(
        self,
        db: Session,
        file_name: str,
        gdf: gpd.GeoDataFrame,
        project_id: UUID,
    ) -> List[Feature]:
        """Creates new vector layer records for features in a feature collection.

        Args:
            db (Session): Database session.
            file_name (str): Original file name.
            gdf (gpd.GeoDataFrame): GeoDataFrame of vector data.
            project_id (UUID): ID of project the vector data belongs to.

        Returns:
            List[Feature]: List of GeoJSON features.
        """
        # Unique ID for feature collection
        layer_id = generate_unique_id()
        # List of vector layer objects
        vector_layers = []
        # Create record in database for each feature
        for _, row in gdf.iterrows():
            # Get geometry in WKT format
            wkt_geometry = row.geometry.wkt
            # Convert to postgis compatible geometry
            geom = func.ST_Force2D(
                func.ST_GeomFromText(text(f"'{wkt_geometry}'"), 4326)
            )
            properties = jsonable_encoder(row.drop("geometry").to_dict())
            # Layer ID will be same for each feature from the feature collection
            vector_layer = VectorLayer(
                layer_name=file_name,
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
            if len(vector_layers) > 0:
                features: List[Feature] = [
                    Feature(**json.loads(feature)) for feature in vector_layers
                ]
                # Create preview image (if one does not exist)
                create_vector_layer_preview(
                    project_id=project_id,
                    layer_id=layer_id,
                    features=features,
                )
                # Deserialize features and create Feature objects for each feature
                return features
            else:
                return []

    def get_vector_layer_by_id_with_metadata(
        self,
        db: Session,
        project_id: UUID,
        data_product_id: UUID,
        layer_id: str,
        metadata_category: str,
    ) -> List[Feature]:
        """Fetches vector layers from feature collection associated with layer ID and
        adds any metadata matching the specified category to the vector
        layer properties.

        Args:
            db (Session): Database session.
            project_id (UUID): Project ID for feature collection.
            data_product_id (UUID): Data product ID for metadata.
            layer_id (str): Layer ID for feature collection.
            metadata_category (str): Metadata category (e.g. "zonal")

        Returns:
            List[Feature]: Features in Feature Collections.
        """
        statement = (
            select(func.ST_AsGeoJSON(VectorLayer), DataProductMetadata)
            .join(VectorLayer.data_product_metadata)
            .where(
                and_(
                    DataProductMetadata.data_product_id == data_product_id,
                    DataProductMetadata.category == metadata_category,
                    VectorLayer.layer_id == layer_id,
                    VectorLayer.project_id == project_id,
                    VectorLayer.is_active,
                )
            )
        )

        with db as session:
            vector_layers = session.execute(statement).all()
            vector_layers_with_metadata_props = []
            for vector_layer in vector_layers:
                vector_layer_geojson_dict = json.loads(vector_layer[0])
                if metadata_category == "zonal":
                    metadata_properties = vector_layer[1].properties["stats"]
                else:
                    metadata_properties = vector_layer[1].properties
                vector_layer_geojson_dict["properties"] = {
                    **vector_layer_geojson_dict["properties"],
                    **metadata_properties,
                }
                vector_layers_with_metadata_props.append(vector_layer_geojson_dict)

            return [
                Feature(**vector_layer)
                for vector_layer in vector_layers_with_metadata_props
            ]

    def get_multi_by_project(
        self, db: Session, project_id: UUID
    ) -> List[Tuple[str, str, str]]:
        """Fetches all vector layers and groups by feature collections.

        Args:
            db (Session): Database session.
            project_id (UUID): Vector layer's project ID.

        Returns:
            List[Tuple[str, str, str]]: List of vector layers with identifying attrs.
        """
        statement = (
            select(
                VectorLayer.layer_id,
                VectorLayer.layer_name,
                func.ST_GeometryType(VectorLayer.geom).label("geometry_type"),
            )
            .where(and_(VectorLayer.project_id == project_id, VectorLayer.is_active))
            .distinct(VectorLayer.layer_id)
        )

        with db as session:
            results = session.execute(statement).all()
            updated_results = [
                (result[0], result[1], get_generic_geometry_type(result[2]))
                for result in results
            ]

            return updated_results

    def get_multi_in_geojson_by_project(
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
                .order_by(VectorLayer.feature_id)
                .where(
                    and_(VectorLayer.project_id == project_id, VectorLayer.is_active)
                )
            ):
                feature = Feature(**json.loads(feature[0]))
                vector_layers[feature.properties["layer_id"]].append(feature)
        for layer_id in vector_layers.keys():
            # Create preview image (if one does not exist)
            preview_img = create_vector_layer_preview(
                project_id=project_id,
                layer_id=layer_id,
                features=vector_layers[layer_id],
            )
        # Each list element is a list of features from a feature collection
        return list(vector_layers.values())

    def remove_layer_by_id(self, db: Session, project_id: UUID, layer_id: str) -> None:
        """_summary_

        Args:
            db (Session): Database session.
            project_id (UUID): Project ID.
            layer_id (str): Layer ID for feature collection.
        """
        with db.begin():
            # Step 1: Set all feature records as inactive
            update_statement = (
                update(VectorLayer)
                .values(is_active=False)
                .where(VectorLayer.layer_id == layer_id)
            )
            db.execute(update_statement)

            # Step 2: Explicitly delete any associated metadata records
            metadata_subquery = (
                select(VectorLayer.feature_id)
                .where(VectorLayer.layer_id == layer_id)
                .scalar_subquery()
            )
            delete_metadata_statement = delete(DataProductMetadata).where(
                DataProductMetadata.vector_layer_feature_id.in_(metadata_subquery)
            )
            db.execute(delete_metadata_statement)

            # Step 3: Delete feature records that are inactive
            delete_statement = delete(VectorLayer).where(
                and_(VectorLayer.layer_id == layer_id, VectorLayer.is_active == False)
            )
            db.execute(delete_statement)

    def verify_user_access_to_vector_layer_by_id(
        self, db: Session, layer_id: str, user_id: UUID
    ) -> bool:
        """Check if user can access a vector layer through project membership.

        Args:
            db (Session): Database session.
            layer_id (str): Layer ID for feature collection.
            user_id (UUID): ID for user.

        Returns:
            bool: True if user can access, False if not.
        """
        statement = select(VectorLayer.project_id).where(
            and_(VectorLayer.layer_id == layer_id, VectorLayer.is_active)
        )
        with db as session:
            project_id = session.scalars(statement).unique().all()
            if len(project_id) == 1:
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_uuid=project_id[0], member_id=user_id
                )
                if project_member:
                    return True
                else:
                    return False
            else:
                return False

        return False


def get_generic_geometry_type(postgis_geom_type: str) -> str:
    """Takes a PostGIS geometry (e.g., ST_Point) and returns a generic
    geometry type (e.g. point).

    Args:
        postgis_geom_type (str): PostGIS geometry type.

    Returns:
        str: Generic geometry type.
    """
    geom_type_mapping = {
        "ST_POINT": "point",
        "ST_MULTIPOINT": "point",
        "ST_LINESTRING": "line",
        "ST_MULTILINESTRING": "line",
        "ST_POLYGON": "polygon",
        "ST_MULTIPOLYGON": "polygon",
    }

    normalized_geom_type = postgis_geom_type.strip().upper()

    return geom_type_mapping.get(normalized_geom_type, "unknown")


vector_layer = CRUDVectorLayer(VectorLayer)
