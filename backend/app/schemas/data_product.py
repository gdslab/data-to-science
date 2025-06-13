from datetime import datetime
from typing import Dict, List, Optional

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    field_validator,
    ValidationInfo,
    UUID4,
)

from app.utils.ImageProcessor import STACProperties

data_type_char_limit_rule = Field(
    None, title="Name of data product's new data type", min_length=1, max_length=16
)


# shared properties
class DataProductBase(BaseModel):
    data_type: Optional[str] = data_type_char_limit_rule
    filepath: Optional[str] = None
    original_filename: Optional[str] = None
    stac_properties: Optional[STACProperties] = None
    is_active: bool = True
    is_initial_processing_completed: bool = False


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    data_type: str
    filepath: str
    original_filename: str
    stac_properties: Optional[STACProperties] = None


# properties to receive via API on update
class DataProductUpdate(DataProductBase):
    pass


class DataProductUpdateDataType(BaseModel):
    data_type: Optional[str] = data_type_char_limit_rule


# properties shared by models stored in DB
class DataProductInDBBase(DataProductBase, from_attributes=True):
    id: UUID4
    data_type: str
    filepath: str
    flight_id: UUID4
    original_filename: str
    stac_properties: Optional[STACProperties] = None
    user_style: Optional[dict] = None
    is_active: bool
    is_initial_processing_completed: bool
    deactivated_at: Optional[datetime] = None


# additional properties to return via API
class DataProductSignature(BaseModel):
    expires: int
    secure: str


class DataProduct(DataProductInDBBase):
    bbox: Optional[List[float]] = None
    crs: Optional[Dict] = None
    resolution: Optional[Dict] = None
    public: bool = False
    signature: Optional[DataProductSignature] = None
    status: Optional[str] = None
    url: Optional[AnyHttpUrl] = None


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass


class DataProductBoundingBox(BaseModel):
    bounds: List[float]


class DataProductBand(BaseModel):
    name: str
    description: str


class DataProductBands(BaseModel):
    bands: List[DataProductBand]


# properties to receive via API on processing tool run
class ProcessingRequest(BaseModel):
    chm: bool
    chmResolution: float = Field(
        ge=0.1,
        title="CHM Resolution",
        description="Spatial resolution for Canopy Height Model processing (0.1-10.0)",
    )
    chmPercentile: int = Field(
        ge=0,
        le=100,
        title="CHM Percentile",
        description="Percentile value for Canopy Height Model processing (0-100)",
    )
    dem_id: Optional[UUID4] = None
    dtm: bool
    dtmResolution: float = Field(
        ge=0.1,
        title="DTM Resolution",
        description="Spatial resolution for Digital Terrain Model processing (0.1-10.0)",
    )
    dtmRigidness: int = Field(
        ge=1,
        le=3,
        title="DTM Rigidness",
        description="Digital Terrain Model rigidness level (1, 2, or 3)",
    )
    exg: bool
    exgRed: int
    exgGreen: int
    exgBlue: int
    hillshade: bool
    ndvi: bool
    ndviNIR: int
    ndviRed: int
    vari: bool
    variRed: int
    variGreen: int
    variBlue: int
    zonal: bool
    zonal_layer_id: str

    @field_validator("dem_id", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Optional[UUID4]) -> Optional[UUID4]:
        """Return None if the string is empty, otherwise return the UUID4."""
        if v == "":
            return None
        return v

    @field_validator("dem_id", mode="before")
    @classmethod
    def validate_dem_id_required(
        cls, v: Optional[UUID4], info: ValidationInfo
    ) -> Optional[UUID4]:
        """Ensure dem_id is set when chm or hillshade is True."""
        if info.data.get("chm") and v is None:
            raise ValueError("dem_id is required when chm is True")
        return v
