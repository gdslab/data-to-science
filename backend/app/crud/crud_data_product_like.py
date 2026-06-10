from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.data_product_like import DataProductLike
from app.schemas.data_product_like import DataProductLikeCreate, DataProductLikeUpdate


class CRUDDataProductLike(
    CRUDBase[DataProductLike, DataProductLikeCreate, DataProductLikeUpdate]
):
    def get_by_data_product_id_and_user_id(
        self, db: Session, data_product_id: UUID, user_id: UUID
    ) -> Optional[DataProductLike]:
        """Get a data product like by data product ID and user ID."""
        statement = (
            select(DataProductLike)
            .join(DataProduct)
            .where(
                DataProduct.is_active,
                DataProductLike.data_product_id == data_product_id,
                DataProductLike.user_id == user_id,
            )
        )

        with db as session:
            return session.scalar(statement)


data_product_like = CRUDDataProductLike(DataProductLike)
