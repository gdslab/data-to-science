from typing_extensions import NotRequired, TypedDict

from pydantic import BaseModel, TypeAdapter


class ImageStructureProps(BaseModel):
    COMPRESSION: str
    INTERLEAVE: str
    LAYOUT: str


class ImageStructure(BaseModel):
    IMAGE_STRUCTURE: ImageStructureProps


class Metadata(BaseModel):
    metadata: ImageStructure


class Stats(TypedDict):
    minimum: float
    maximum: float
    mean: float
    stddev: float


class STACRasterProperties(TypedDict):
    data_type: str
    stats: Stats
    nodata: NotRequired[int | float | None]
    unit: NotRequired[str | None]


class STACEOProperties(TypedDict):
    name: str
    description: str


class STACProperties(TypedDict):
    raster: list[STACRasterProperties]
    eo: list[STACEOProperties]


STACPropertiesValidator = TypeAdapter(STACProperties)
