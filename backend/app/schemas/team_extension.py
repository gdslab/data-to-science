from pydantic import BaseModel, UUID4


# shared properties
class TeamExtensionBase(BaseModel):
    pass


# properties required on creation
class TeamExtensionCreate(TeamExtensionBase):
    pass


# properties shared by models in DB
class TeamExtensionInDBBase(TeamExtensionBase, from_attributes=True):
    id: UUID4
    extension_id: UUID4
    team_id: UUID4


# additional properties returned by crud
class TeamExtension(TeamExtensionInDBBase):
    pass


# additional properties stored in DB
class TeamExtensionInDB(TeamExtensionInDBBase):
    pass
