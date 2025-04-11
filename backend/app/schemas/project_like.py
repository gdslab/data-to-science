from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Shared properties
class ProjectLikeBase(BaseModel):
    project_id: Optional[UUID4] = None
    user_id: Optional[UUID4] = None


# Properties required on creation
class ProjectLikeCreate(ProjectLikeBase):
    project_id: UUID4
    user_id: UUID4


# Properties required on update
class ProjectLikeUpdate(ProjectLikeBase):
    pass


# Properties in database
class ProjectLikeInDBBase(ProjectLikeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    user_id: UUID4
    project_id: UUID4


# Properties returned by CRUD
class ProjectLike(ProjectLikeInDBBase):
    pass
