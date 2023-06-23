from typing import TYPE_CHECKING

from pydantic import BaseModel


if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


# shared properties
class UserBase(BaseModel):
    # do not want to require properties during update
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None

    is_approved: bool = False


# properties to receive via API on creation
class UserCreate(UserBase):
    # all required during creation
    email: EmailStr
    password: str
    first_name: str
    last_name: str


# properties to receive via API on update
class UserUpdate(UserBase):
    # provide option to update password during update
    password: str | None = None


# properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int

    class Config:
        orm_mode = True


# additional properties to return via API
class User(UserInDBBase):
    pass


# additional properties stored in DB
class UserInDB(UserInDBBase):
    
    hashed_password: str
