from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Shared properties
class ProjectModuleBase(BaseModel):
    enabled: Optional[bool] = None


# Properties required on creation
class ProjectModuleCreate(ProjectModuleBase):
    pass


# Properties required on update
class ProjectModuleUpdate(ProjectModuleBase):
    enabled: bool


# Properties in database
class ProjectModuleInDBBase(ProjectModuleBase):
    model_config = ConfigDict(from_attributes=True)

    description: Optional[str] = None
    enabled: bool
    id: UUID4
    label: Optional[str] = None
    module_name: str
    project_id: UUID4
    required: Optional[bool] = None
    sort_order: Optional[int] = None


# Properties returned by CRUD
class ProjectModule(ProjectModuleInDBBase):
    pass
