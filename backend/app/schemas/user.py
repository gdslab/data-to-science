from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from pydantic import AnyHttpUrl, BaseModel, UUID4


if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


# shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_email_confirmed: bool = False
    is_approved: bool = False


# properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


# properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


# properties shared by models stored in DB
class UserInDBBase(UserBase, from_attributes=True):
    id: UUID4
    created_at: datetime


# additional properties to return via API
class User(UserInDBBase):
    api_access_token: Optional[str] = None
    exts: List[str] = []
    is_superuser: bool
    profile_url: Optional[AnyHttpUrl] = None


# additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
    is_superuser: bool
