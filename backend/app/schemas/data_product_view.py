from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Shared properties
class DataProductViewBase(BaseModel):
    data_product_id: Optional[UUID4] = None
    user_id: Optional[UUID4] = None
    session_id: Optional[str] = None


# Properties required on creation
class DataProductViewCreate(DataProductViewBase):
    data_product_id: UUID4


# Properties required on update
class DataProductViewUpdate(DataProductViewBase):
    pass


# Properties in database
class DataProductViewInDBBase(DataProductViewBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    data_product_id: UUID4
    viewed_at: datetime


# Properties returned by CRUD
class DataProductView(DataProductViewInDBBase):
    pass
