import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.base_class import Base


if TYPE_CHECKING:
    from .project_member import ProjectMember
    from .team import Team
    from .user import User


class IndoorProject(Base):
    __tablename__ = "indoor_projects"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # foreign keys
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # relationships
    owner: Mapped["User"] = relationship(back_populates="indoor_projects")
    team: Mapped["Team"] = relationship(back_populates="indoor_projects")
    indoor_members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="indoor_project",
        cascade="all, delete-orphan",
        primaryjoin="and_(ProjectMember.project_type == 'INDOOR_PROJECT', ProjectMember.project_uuid == IndoorProject.id)",
        foreign_keys="[ProjectMember.project_uuid]",
    )

    def __repr__(self) -> str:
        return (
            f"IndoorProject(id={self.id!r}, title={self.title!r}, "
            f"description={self.description!r}, start_date={self.start_date!r}, "
            f"end_date={self.end_date!r}, is_active={self.is_active!r}, "
            f"deactivated_at={self.deactivated_at!r}, owner_id={self.owner_id!r}, "
            f"team_id={self.team_id!r})"
        )
