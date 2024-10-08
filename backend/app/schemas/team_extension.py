from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


# shared properties
class TeamExtensionBase(BaseModel):
    is_active: Optional[bool] = None
    extension_id: Optional[UUID4] = None
    team_id: Optional[UUID4] = None


# properties required on creation
class TeamExtensionCreate(TeamExtensionBase):
    is_active: bool = False
    extension_id: UUID4
    team_id: UUID4


class TeamExtensionUpdate(TeamExtensionBase):
    deactivated_at: Optional[datetime] = None
    is_active: bool = False
    extension_id: UUID4
    team_id: UUID4


# properties shared by models in DB
class TeamExtensionInDBBase(TeamExtensionBase, from_attributes=True):
    id: UUID4
    deactivated_at: Optional[datetime] = None
    is_active: bool
    extension_id: UUID4
    team_id: UUID4


# additional properties returned by crud
class TeamExtension(TeamExtensionInDBBase):
    pass


# additional properties stored in DB
class TeamExtensionInDB(TeamExtensionInDBBase):
    pass
