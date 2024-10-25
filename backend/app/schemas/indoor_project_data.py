from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, UUID4


class IndoorProjectDataBase(BaseModel):
    """
    Base model for indoor project data, containing commo attributes.
    """

    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    directory_structure: Optional[Dict] = None
    upload_date: Optional[datetime] = None


class IndoorProjectDataCreate(IndoorProjectDataBase):
    """
    Creation model for indoor project data, containing required attributes.
    """

    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_date: datetime


class IndoorProjectDataUpdate(IndoorProjectDataBase):
    """
    Update model for indoor project data, inheriting common attributes.
    """

    pass


class IndoorProjectDataInDBBase(IndoorProjectDataBase):
    """
    DB model for indoor project data, containing common attributes and internally
    generated attributes.
    """

    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_date: datetime
    # internal
    id: UUID4
    indoor_project_id: UUID4
    uploader_id: UUID4 = Field(exclude=True)
    is_active: bool = Field(exclude=True)
    deactivated_at: Optional[datetime] = Field(default=None, exclude=True)


class IndoorProjectData(IndoorProjectDataInDBBase):
    """
    API model for indoor project data, containing common attributes and
    additional API exclusive attributes.
    """

    pass
