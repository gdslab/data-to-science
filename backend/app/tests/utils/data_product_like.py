from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.data_product_like import DataProductLike
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.user import create_user


def create_data_product_like(
    db: Session,
    data_product_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
) -> DataProductLike:
    """Create a DataProductLike row for testing."""
    if data_product_id is None:
        sample = SampleDataProduct(db)
        data_product_id = sample.obj.id
    if user_id is None:
        user_id = create_user(db).id

    return crud.data_product_like.create(
        db,
        obj_in=schemas.DataProductLikeCreate(
            data_product_id=data_product_id,
            user_id=user_id,
        ),
    )
