from pydantic import BaseModel, UUID4


# shared properties
class ExtensionBase(BaseModel):
    name: str | None = None


# properties required on creation
class ExtensionCreate(ExtensionBase):
    name: str


# properties shared by models in DB
class ExtensionInDBBase(ExtensionBase, from_attributes=True):
    id: UUID4
    name: str


# additional properties returned by crud
class Extension(ExtensionInDBBase):
    pass


# additional properties stored in DB
class ExtensionInDB(ExtensionInDBBase):
    pass
