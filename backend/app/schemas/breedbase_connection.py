from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Shared properties
class BreedbaseConnectionBase(BaseModel):
    base_url: Optional[str] = None
    study_id: Optional[str] = None


# Properties required on creation
class BreedbaseConnectionCreate(BreedbaseConnectionBase):
    base_url: str
    study_id: str


# Properties required on update
class BreedbaseConnectionUpdate(BreedbaseConnectionBase):
    pass


# Properties in database
class BreedbaseConnectionInDBBase(BreedbaseConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    base_url: str
    study_id: str
    project_id: UUID4


# Properties returned by CRUD
class BreedbaseConnection(BreedbaseConnectionInDBBase):
    pass
