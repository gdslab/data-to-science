from typing import Dict, List
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product_metadata import DataProductMetadata
from app.models.vector_layer import VectorLayer
from app.schemas.data_product_metadata import (
    DataProductMetadataCreate,
    DataProductMetadataUpdate,
)


class CRUDDataProductMetadata(
    CRUDBase[DataProductMetadata, DataProductMetadataCreate, DataProductMetadataUpdate]
):
    def create_with_data_product(
        self, db: Session, obj_in: DataProductMetadataCreate, data_product_id: UUID
    ) -> DataProductMetadata:
        obj_in_json = jsonable_encoder(obj_in)
        metadata = DataProductMetadata(**obj_in_json, data_product_id=data_product_id)
        with db as session:
            session.add(metadata)
            session.commit()
            session.refresh(metadata)
        return metadata

    def get_by_data_product(
        self,
        db: Session,
        category: str,
        data_product_id: UUID,
        vector_layer_id: UUID | None = None,
    ) -> List[DataProductMetadata]:
        if vector_layer_id:
            metadata_query = select(DataProductMetadata).where(
                and_(
                    DataProductMetadata.category == category,
                    DataProductMetadata.data_product_id == data_product_id,
                    DataProductMetadata.vector_layer_id == vector_layer_id,
                )
            )
        else:
            metadata_query = select(DataProductMetadata).where(
                and_(
                    DataProductMetadata.category == category,
                    DataProductMetadata.data_product_id == data_product_id,
                )
            )
        with db as session:
            metadata = session.scalars(metadata_query).all()
            return metadata

    def get_zonal_statistics_by_layer_id(
        self, db: Session, data_product_id: UUID, layer_id: str
    ) -> Dict:
        zonal_statistics_query = (
            select(DataProductMetadata)
            .join(DataProductMetadata.vector_layer)
            .where(
                and_(
                    DataProductMetadata.category == "zonal",
                    DataProductMetadata.data_product_id == data_product_id,
                    VectorLayer.layer_id == layer_id,
                )
            )
        )
        zonal_statistics_and_props = []
        with db as session:
            all_metadata = session.scalars(zonal_statistics_query).all()
            if len(all_metadata) > 0:
                for metadata in all_metadata:
                    vector_layer_props = metadata.vector_layer.properties
                    zonal_stats = metadata.properties["stats"]
                    zonal_statistics_and_props.append(
                        {**vector_layer_props, **zonal_stats}
                    )

            return zonal_statistics_and_props


data_product_metadata = CRUDDataProductMetadata(DataProductMetadata)
