from uuid import UUID

from pydantic import BaseModel


# shared properties
class UserStyleBase(BaseModel):
    settings: dict | None = None


# properties to receive via API on creation
class UserStyleCreate(UserStyleBase):
    settings: dict


# properties to receive via API on update
class UserStyleUpdate(UserStyleBase):
    settings: dict


# properties shared by models stored in DB
class UserStyleInDBBase(UserStyleBase, from_attributes=True):
    id: UUID
    settings: dict
    data_product_id: UUID
    user_id: UUID


# additional properties to return via API
class UserStyle(UserStyleInDBBase):
    pass


# additional properties stored in DB
class UserStyleInDB(UserStyleInDBBase):
    pass
