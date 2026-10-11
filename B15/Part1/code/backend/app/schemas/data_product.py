from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union

from pydantic import (
    UUID4,
    AnyHttpUrl,
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
)

from app.utils.stac import STACProperties

data_type_char_limit_rule = Field(
    None, title="Name of data product's new data type", min_length=1, max_length=16
)


# shared properties
class DataProductBase(BaseModel):
    data_type: Optional[str] = data_type_char_limit_rule
    filepath: Optional[str] = None
    original_filename: Optional[str] = None
    stac_properties: Optional[STACProperties] = None
    file_size: Optional[int] = None
    is_active: bool = True
    is_initial_processing_completed: bool = False


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    data_type: str
    filepath: str
    original_filename: str
    stac_properties: Optional[STACProperties] = None
    raw_data_id: Optional[UUID4] = None


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
    raw_data_id: Optional[UUID4] = None
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


class DataProductXMLMetadata(BaseModel):
    original_filename: str
    file_size: int
    content: str


class DataProduct(DataProductInDBBase):
    bbox: Optional[List[float]] = None
    crs: Optional[Dict] = None
    # Safe name for downloads, built from the project, flight date, and data
    # type. Never derived from original_filename.
    download_filename: Optional[str] = None
    resolution: Optional[Dict] = None
    public: bool = False
    signature: Optional[DataProductSignature] = None
    status: Optional[str] = None
    url: Optional[AnyHttpUrl] = None
    liked: bool = False
    like_count: int = 0
    view_count: int = 0
    xml_metadata: Optional[DataProductXMLMetadata] = None


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass


class DataProductBoundingBox(BaseModel):
    bounds: List[float]


class DataProductPointValue(BaseModel):
    coordinates: List[float]
    values: List[Optional[float]]


class DataProductBand(BaseModel):
    name: str
    description: str


class DataProductBands(BaseModel):
    bands: List[DataProductBand]


# Symbology values reach GDAL as command arguments and as color table entries,
# so they are validated as finite numbers here rather than coerced later. Without
# this, a value of the wrong type raises deep inside the export and surfaces as a
# 500, and "inf"/"nan" parse cleanly into a color table GDAL cannot use.
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class SymbologyBand(BaseModel):
    """One color channel of a multiband symbology.

    Mirrors the map's ColorBand type in RasterSymbologyContext.tsx.
    """

    idx: Optional[int] = None
    min: Optional[FiniteFloat] = None
    max: Optional[FiniteFloat] = None
    userMin: Optional[FiniteFloat] = None
    userMax: Optional[FiniteFloat] = None


class SymbologyCommon(BaseModel):
    """Settings shared by both symbology shapes.

    Every field is optional because saved user styles predate some of them, and
    the export already falls back to a default range when values are missing.
    Unrecognized keys are ignored rather than rejected, so the map can keep
    sending fields the export does not use (such as a background data product).
    """

    mode: Optional[str] = None
    meanStdDev: Optional[FiniteFloat] = None
    opacity: Optional[FiniteFloat] = None


class SingleBandSymbologySettings(SymbologyCommon):
    """Single band symbology, identified by its color ramp.

    Mirrors the map's SingleBandSymbology type in RasterSymbologyContext.tsx.
    """

    # Required and non-empty: it is what tells this shape apart from the
    # multiband one, and an empty ramp name has nothing to look up
    colorRamp: Annotated[str, Field(min_length=1)]
    nodata: Optional[FiniteFloat] = None
    min: Optional[FiniteFloat] = None
    max: Optional[FiniteFloat] = None
    userMin: Optional[FiniteFloat] = None
    userMax: Optional[FiniteFloat] = None


class MultibandSymbologySettings(SymbologyCommon):
    """Multiband symbology, identified by its three color channels.

    Mirrors the map's MultibandSymbology type in RasterSymbologyContext.tsx.
    """

    red: SymbologyBand
    green: SymbologyBand
    blue: SymbologyBand


# properties to receive via API on raster export
class RasterExportRequest(BaseModel):
    # Symbology settings from the map. Same shape as UserStyle settings. When
    # omitted, the raster is exported without any symbology applied. The two
    # shapes are told apart by their required fields: only single band settings
    # carry a colorRamp, and only multiband settings carry red/green/blue.
    settings: Optional[
        Union[SingleBandSymbologySettings, MultibandSymbologySettings]
    ] = None


# properties to receive via API on processing tool run
class ProcessingRequest(BaseModel):
    chm: bool
    chmResolution: float = Field(
        ge=0.1,
        title="CHM Resolution",
        description="Spatial resolution for Canopy Height Model processing (0.1-10.0)",
    )
    chmPercentile: float = Field(
        ge=0.0,
        le=100.0,
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
