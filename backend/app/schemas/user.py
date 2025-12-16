from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, UUID4, field_validator


if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


# shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    registration_intent: Optional[str] = Field(None, min_length=20, max_length=500)
    is_approved: bool = False
    is_demo: bool = False
    is_email_confirmed: bool = False

    @field_validator("first_name", "last_name", "registration_intent", mode="before")
    @classmethod
    def normalize_string_fields(cls, value: Optional[str]) -> Optional[str]:
        """Strip whitespace and convert empty strings to None."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None


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
class UserInDBBase(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    created_at: datetime


# additional properties to return via API
class User(UserInDBBase):
    api_access_token: Optional[str] = None
    exts: List[str] = []
    is_superuser: bool
    profile_url: Optional[AnyHttpUrl] = None
    # exclude from api responses
    is_demo: bool = Field(exclude=True)


# public properties for non-admin user list endpoint
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_url: Optional[AnyHttpUrl] = None


# admin properties for admin user list endpoint
class UserAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    profile_url: Optional[AnyHttpUrl] = None
    exts: List[str] = []
    is_approved: bool = False
    is_email_confirmed: bool = False


# additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
    is_superuser: bool
