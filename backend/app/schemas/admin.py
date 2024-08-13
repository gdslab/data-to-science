from typing import Optional

from pydantic import BaseModel


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
    storage_availability: StorageAvailability
    user_count: int
