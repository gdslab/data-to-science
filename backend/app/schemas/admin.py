from pydantic import BaseModel


class DataProductDtypeCounts(BaseModel):
    dsm_count: int
    ortho_count: int
    point_cloud_count: int
    other_count: int


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
