from typing import Optional

from pydantic import BaseModel, UUID4


class DataProductDtypeCount(BaseModel):
    name: str
    count: int


class DataProductDtypeCounts(BaseModel):
    first: Optional[DataProductDtypeCount] = None
    second: Optional[DataProductDtypeCount] = None
    third: Optional[DataProductDtypeCount] = None
    other: Optional[DataProductDtypeCount] = None


class StorageAvailability(BaseModel):
    total: float
    used: float
    free: float


class SiteStatistics(BaseModel):
    data_product_count: int
    data_product_dtype_count: DataProductDtypeCounts
    flight_count: int
    project_count: int
    public_data_product_count: int
    storage_availability: StorageAvailability
    user_count: int


class UserProjectStatistics(BaseModel):
    id: UUID4
    user: str
    total_projects: int
    total_active_projects: int
    total_storage: int
    total_active_storage: int
