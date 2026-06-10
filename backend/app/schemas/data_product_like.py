from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Shared properties
class DataProductLikeBase(BaseModel):
    data_product_id: Optional[UUID4] = None
    user_id: Optional[UUID4] = None


# Properties required on creation
class DataProductLikeCreate(DataProductLikeBase):
    data_product_id: UUID4
    user_id: UUID4


# Properties required on update
class DataProductLikeUpdate(DataProductLikeBase):
    pass


# Properties in database
class DataProductLikeInDBBase(DataProductLikeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    user_id: UUID4
    data_product_id: UUID4


# Properties returned by CRUD
class DataProductLike(DataProductLikeInDBBase):
    pass
