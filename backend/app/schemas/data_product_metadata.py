from typing import Dict, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# shared properties
class DataProductMetadataBase(BaseModel):
    category: str | None = None
    properties: dict | None = None


# properties to receive via API on creation
class DataProductMetadataCreate(DataProductMetadataBase):
    category: str
    properties: dict
    vector_layer_id: UUID | None = None


# properties to receive via API on update
class DataProductMetadataUpdate(DataProductMetadataBase):
    pass


# properties shared by models stored in DB
class DataProductMetadataInDBBase(DataProductMetadataBase, from_attributes=True):
    id: UUID
    category: str
    properties: dict

    data_product_id: UUID
    vector_layer_id: UUID | None = None


# additional properties to return via API
class DataProductMetadata(DataProductMetadataInDBBase):
    pass


# additional properties stored in DB
class DataProductMetadataInDB(DataProductMetadataInDBBase):
    pass


class ZonalStatistics(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std: float
    count: int


class ZonalStatisticsProps(ZonalStatistics):
    model_config = ConfigDict(extra="allow")
