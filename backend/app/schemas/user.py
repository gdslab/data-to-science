from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, EmailStr


# shared properties
class UserBase(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_approved: bool | None = False


# properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


# properties to receive via API on update
class UserUpdate(UserBase):
    password: str | None = None


class UserInDBBase(UserBase):
    # add database properties here that 
    # should be returned via API in User
    class Config:
        orm_mode = True


# additional properties to return via API
class User(UserInDBBase):
    pass


# additional properties stored in DB
class UserInDB(UserInDBBase):
    id: int
    hashed_password: str
    is_superuser: bool = False
