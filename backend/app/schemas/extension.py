from pydantic import BaseModel, UUID4


# shared properties
class ExtensionBase(BaseModel):
    description: str | None = None
    name: str | None = None


# properties required on creation
class ExtensionCreate(ExtensionBase):
    description: str | None = None
    name: str


# properties required on update
class ExtensionUpdate(ExtensionBase):
    description: str | None = None
    name: str | None = None


# properties shared by models in DB
class ExtensionInDBBase(ExtensionBase, from_attributes=True):
    id: UUID4
    description: str | None = None
    name: str


# additional properties returned by crud
class Extension(ExtensionInDBBase):
    pass


# additional properties stored in DB
class ExtensionInDB(ExtensionInDBBase):
    pass
