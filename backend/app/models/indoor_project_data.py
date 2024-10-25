import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class IndoorProjectData(Base):
    __tablename__ = "indoor_project_data"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stored_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    directory_structure: Mapped[dict] = mapped_column(JSONB, nullable=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # foreign keys
    indoor_project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indoor_projects.id"), nullable=False
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"IndoorProjectData(id={self.id!r}, original_filename={self.original_filename!r}, "
            f"stored_filename={self.stored_filename!r}, file_path={self.file_path!r}, "
            f"file_size={self.file_size!r}, file_type={self.file_type!r}, "
            f"directory_structure={self.directory_structure!r}, "
            f"upload_date={self.upload_date!r}, is_active={self.is_active!r}, "
            f"deactivated_at={self.deactivated_at!r}, "
            f"indoor_project_id={self.indoor_project_id!r}, "
            f"uploader_id={self.uploader_id!r})"
        )
