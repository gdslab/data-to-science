from typing import Any, Optional, TypeVar
from uuid import UUID

from geojson_pydantic import FeatureCollection
from pydantic import AnyHttpUrl, BaseModel


Props = TypeVar("Props", bound=dict[str, Any] | BaseModel)


class VectorLayerBase(BaseModel):
    layer_name: str | None = None
    geojson: FeatureCollection | None = None


class VectorLayerCreate(VectorLayerBase):
    layer_name: str
    geojson: FeatureCollection


class VectorLayerUpdate(VectorLayerBase):
    layer_name: str


class VectorLayerInDBBase(VectorLayerBase, from_attributes=True):
    feature_id: UUID
    layer_name: str
    geojson: FeatureCollection
    project_id: UUID
    flight_id: UUID | None
    data_product_id: UUID | None


class VectorLayer(VectorLayerInDBBase):
    pass


class VectorLayerInDB(VectorLayerInDBBase):
    pass


class Metadata(BaseModel):
    preview_url: Optional[AnyHttpUrl]


class VectorLayerFeatureCollection(FeatureCollection):
    metadata: Metadata


class VectorLayerPayload(BaseModel):
    layer_id: str
    layer_name: str
    geom_type: str
    signed_url: AnyHttpUrl
    preview_url: AnyHttpUrl
    parquet_url: AnyHttpUrl
    fgb_url: AnyHttpUrl
