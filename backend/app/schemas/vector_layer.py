from typing import Any, TypeVar
from uuid import UUID

from geojson_pydantic import FeatureCollection
from pydantic import BaseModel


Props = TypeVar("Props", bound=dict[str, Any] | BaseModel)


class VectorLayerBase(BaseModel):
    layer_name: str | None = None
    geojson: FeatureCollection | None = None


class VectorLayerCreate(VectorLayerBase):
    layer_name: str
    geojson: FeatureCollection


class VectorLayerUpdate(VectorLayerBase):
    pass


class VectorLayerInDBBase(VectorLayerBase, from_attributes=True):
    id: UUID
    layer_name: str
    geojson: FeatureCollection
    project_id: UUID
    flight_id: UUID | None
    data_product_id: UUID | None


class VectorLayer(VectorLayerInDBBase):
    pass


class VectorLayerInDB(VectorLayerInDBBase):
    pass
