from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Extra, Field, field_validator, RootModel, UUID4


class IndoorProjectDataBase(BaseModel):
    """
    Base model for indoor project data, containing commo attributes.
    """

    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    directory_structure: Optional[Dict] = None
    upload_date: Optional[datetime] = None


class IndoorProjectDataCreate(IndoorProjectDataBase):
    """
    Creation model for indoor project data, containing required attributes.
    """

    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_date: datetime


class IndoorProjectDataUpdate(IndoorProjectDataBase):
    """
    Update model for indoor project data, inheriting common attributes.
    """

    pass


class IndoorProjectDataInDBBase(IndoorProjectDataBase):
    """
    DB model for indoor project data, containing common attributes and internally
    generated attributes.
    """

    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_date: datetime
    # internal
    id: UUID4
    indoor_project_id: UUID4
    uploader_id: UUID4 = Field(exclude=True)
    is_active: bool = Field(exclude=True)
    deactivated_at: Optional[datetime] = Field(default=None, exclude=True)


class IndoorProjectData(IndoorProjectDataInDBBase):
    """
    API model for indoor project data, containing common attributes and
    additional API exclusive attributes.
    """

    pass


class IndoorProjectDataSpreadsheetSummary(BaseModel):
    exp_id: List[int]
    treatment: List[str]
    species_name: List[str]
    entry: List[str]
    pot_barcode: List[int]
    planting_date: List[datetime]
    pottype: List[str]
    ct_configuration: List[str]
    variety: List[str]
    year: List[int]
    location: List[str]
    pi: List[str]


class IndoorProjectDataPlant(BaseModel):
    """
    API model for individual indoor project plant.
    """

    exp_id: int
    treatment: str
    species_name: str
    entry: str
    planting_date: datetime
    pottype: str
    ct_configuration: str
    variety: str
    year: int
    location: str
    pi: str


class IndoorProjectDataPlantSide(BaseModel):
    filename: str
    exp_id: int
    pot_barcode: int
    variety: str
    treatment: str
    scan_time: str
    scan_date: date
    dfp: int
    view: str
    frame_nr: int
    width: int
    height: int
    surface: int
    convex_hull: int
    roundness: int
    center_of_mass_distance: int
    center_of_mass_x: int
    center_of_mass_y: int
    hue: int
    saturation: int
    intensity: int
    fluorescence: int


class IndoorProjectDataPlantTop(BaseModel):
    filename: str
    exp_id: int
    pot_barcode: int
    variety: str
    treatment: str
    scan_time: str
    scan_date: date
    dfp: int
    angle: int
    surface: int
    convex_hull: int
    roundness: int
    center_of_mass_distance: int
    center_of_mass_x: int
    center_of_mass_y: int
    hue: int
    saturation: int
    intensity: int
    fluorescence: int

    class Config:
        extra = Extra.allow  # allows h0, h1, h2, etc. fields to be dynamically added

    @classmethod
    def validate_dynamic_hue_fields(cls, values: Dict[str, int]) -> Dict[str, int]:
        for key in values:
            if key.startswith("h") and key[1:].isdigit():
                index = int(key[1:])
                if not (0 <= index <= 359):
                    raise ValueError(
                        f"Invalid key {key}. Expected keys to follow 'h0' to 'h359'."
                    )
        return values

    @classmethod
    def validate_dynamic_saturation_fields(
        cls, values: Dict[str, int]
    ) -> Dict[str, int]:
        for key in values:
            if key.startswith("s") and key[1:].isdigit():
                index = int(key[1:])
                if not (0 <= index <= 99):
                    raise ValueError(
                        f"Invalid key {key}. Expected keys to follow 's0' to 's99'."
                    )
        return values

    @classmethod
    def validate_dynamic_intensity_fields(
        cls, values: Dict[str, int]
    ) -> Dict[str, int]:
        for key in values:
            if key.startswith("v") and key[1:].isdigit():
                index = int(key[1:])
                if not (0 <= index <= 99):
                    raise ValueError(
                        f"Invalid key {key}. Expected keys to follow 'v0' to 'v99'."
                    )
        return values

    @classmethod
    def validate_dynamic_fluorescence_fields(
        cls, values: Dict[str, int]
    ) -> Dict[str, int]:
        for key in values:
            if key.startswith("f") and key[1:].isdigit():
                index = int(key[1:])
                if not (0 <= index <= 99):
                    raise ValueError(
                        f"Invalid key {key}. Expected keys to follow 'f0' to 'f99'."
                    )
        return values


class IndoorProjectDataSpreadsheetPlantData(BaseModel):
    ppew: IndoorProjectDataPlant
    top: List[IndoorProjectDataPlantTop]
    side: List[IndoorProjectDataPlantSide]


class IndoorProjectDataSpreadsheetData(RootModel[Dict[int, IndoorProjectDataPlant]]):
    pass


class IndoorProjectDataSpreadsheet(BaseModel):
    """
    API model for indoor project spreadsheet data.
    """

    records: IndoorProjectDataSpreadsheetData
    summary: IndoorProjectDataSpreadsheetSummary
