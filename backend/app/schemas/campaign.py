from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NewColumn(BaseModel):
    name: str
    fill: str


class Timepoint(BaseModel):
    numberOfSamples: int
    sampleNames: list[str | int]
    timepointIdentifier: str


class Measurement(BaseModel):
    name: str
    units: str
    timepoints: list[Timepoint]


class Treatment(BaseModel):
    name: str
    filenames: list[str]
    data: list
    columns: list


class CampaignFormData(BaseModel):
    measurements: list[Measurement]
    newColumns: list[NewColumn]
    templateInput: list[str]
    treatments: list[Treatment]


# shared properties
class CampaignBase(BaseModel):
    lead_id: UUID | None = None
    form_data: CampaignFormData | None = None
    is_active: bool = True


# properties to receive via API on creation
class CampaignCreate(CampaignBase):
    lead_id: UUID


# properties to receive via API on update
class CampaignUpdate(CampaignBase):
    # same as base model
    pass


# properties shared by models stored in DB
class CampaignInDBBase(CampaignBase, from_attributes=True):
    id: UUID
    lead_id: UUID
    form_data: CampaignFormData | None
    project_id: UUID
    is_active: bool
    deactivated_at: datetime | None


# additional properties to return via API
class Campaign(CampaignInDBBase):
    # no additional props
    pass


# additional properties stored in DB
class CampaignInDB(CampaignInDBBase):
    # no additional props
    pass


# additional schemas used when creating AgTC templates
class CampaignTemplateConfig(BaseModel):
    newColumns: list
    sampleIdentifiers: list
    sampleNames: list
    templateInput: list
    templateOutput: list


class CampaignTimepoint(BaseModel):
    measurement: int
    timepoint: int
    treatment: int


class CampaignTemplateCreate(BaseModel):
    timepoints: list[CampaignTimepoint]
