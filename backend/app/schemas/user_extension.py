from pydantic import BaseModel, UUID4


# shared properties
class UserExtensionBase(BaseModel):
    pass


# properties required on creation
class UserExtensionCreate(UserExtensionBase):
    extension_id: UUID4
    user_id: UUID4


# properties shared by models in DB
class UserExtensionInDBBase(UserExtensionBase, from_attributes=True):
    id: UUID4
    extension_id: UUID4
    user_id: UUID4


# additional properties returned by crud
class UserExtension(UserExtensionInDBBase):
    pass


# additional properties stored in DB
class UserExtensionInDB(UserExtensionInDBBase):
    pass
