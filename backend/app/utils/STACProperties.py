from typing_extensions import NotRequired, TypedDict

from pydantic import TypeAdapter


class Histogram(TypedDict):
    count: int
    min: float
    max: float
    buckets: list[int]


class Stats(TypedDict):
    minimum: float
    maximum: float
    mean: float
    stddev: float


class STACRasterProperties(TypedDict):
    data_type: str
    stats: dict[str, float]
    histogram: Histogram
    nodata: NotRequired[int | float | None]
    unit: NotRequired[str | None]


class STACEOProperties(TypedDict):
    name: str
    description: str


class STACProperties(TypedDict):
    raster: list[STACRasterProperties]
    eo: list[STACEOProperties]


STACPropertiesValidator = TypeAdapter(STACProperties)
