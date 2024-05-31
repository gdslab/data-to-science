from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product_metadata import DataProductMetadata
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
    ) -> list[DataProductMetadata] | None:
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


data_product_metadata = CRUDDataProductMetadata(DataProductMetadata)
