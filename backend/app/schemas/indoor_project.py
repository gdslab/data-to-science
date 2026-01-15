from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, ValidationInfo, UUID4


class Role(Enum):
    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"


class IndoorProjectBase(BaseModel):
    """
    Base model for indoor projects, containing common attributes.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_id: Optional[UUID4] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Union[str, datetime, None]) -> Union[datetime, None]:
        """Convert empty strings to None to handle form inputs."""
        if v == "" or v is None:
            return None
        return v

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(
        cls, v: Optional[datetime], info: ValidationInfo
    ) -> Optional[datetime]:
        if (
            "start_date" in info.data
            and v is not None
            and info.data["start_date"] is not None
            and v < info.data["start_date"]
        ):
            raise ValueError("end_date cannot be before start_date")
        return v


class IndoorProjectCreate(IndoorProjectBase):
    """
    Creation model for indoor projects, containing required attributes.
    """

    title: str
    description: str


class IndoorProjectUpdate(IndoorProjectBase):
    """
    Update model for indoor projects, inheriting common attributes.
    """

    pass


class IndoorProjectInDBBase(IndoorProjectBase):
    """
    DB model for indoor projects, containing common attributes and internally
    generated attributes.
    """

    title: str
    description: str
    # internal
    id: UUID4
    is_active: bool = Field(exclude=True)
    deactivated_at: Optional[datetime] = Field(default=None, exclude=True)
    owner_id: UUID4 = Field(exclude=True)


class IndoorProject(IndoorProjectInDBBase):
    """
    API model for indoor projects, containing common attributes and
    additional API exclusive attributes.
    """

    # properties created after queries
    role: Role = Role.VIEWER
