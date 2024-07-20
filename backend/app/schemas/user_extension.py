from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


# shared properties
class UserExtensionBase(BaseModel):
    is_active: Optional[bool] = None
    extension_id: Optional[UUID4] = None
    user_id: Optional[UUID4] = None


# properties required on creation
class UserExtensionCreate(UserExtensionBase):
    is_active: bool = False
    extension_id: UUID4
    user_id: UUID4


class UserExtensionUpdate(UserExtensionBase):
    deactivated_at: Optional[datetime] = None
    is_active: bool = False
    extension_id: UUID4
    user_id: UUID4


# properties shared by models in DB
class UserExtensionInDBBase(UserExtensionBase, from_attributes=True):
    id: UUID4
    deactivated_at: Optional[datetime] = None
    is_active: bool
    extension_id: UUID4
    user_id: UUID4


# additional properties returned by crud
class UserExtension(UserExtensionInDBBase):
    pass


# additional properties stored in DB
class UserExtensionInDB(UserExtensionInDBBase):
    pass
