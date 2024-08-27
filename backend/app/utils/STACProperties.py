from typing_extensions import NotRequired, TypedDict, Union

import numpy as np
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


class STACRasterPropertiesBase(TypedDict):
    data_type: str
    stats: Stats
    nodata: NotRequired[Union[int, float, str, None]]
    unit: NotRequired[Union[str, None]]


class STACRasterProperties(STACRasterPropertiesBase):
    @staticmethod
    def validate_nodata(properties: "STACRasterProperties") -> "STACRasterProperties":
        # convert numpy nan to string before storing in database
        if "nodata" in properties and np.isnan(properties["nodata"]):
            properties["nodata"] = "nan"
        return properties


class STACEOProperties(TypedDict):
    name: str
    description: str


class STACProperties(TypedDict):
    raster: list[STACRasterProperties]
    eo: list[STACEOProperties]


STACPropertiesValidator = TypeAdapter(STACProperties)
