import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .team import Team
    from .user import User


ROLES = ["Standard", "Manager"]


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[enumerate] = mapped_column(
        ENUM(*ROLES, name="role_type"), default="Standard", nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    member: Mapped["User"] = relationship(back_populates="team_memberships")
    team: Mapped["Team"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return (
            f"TeamMember(id={self.id!r}, role={self.role!r}, "
            f"member_id={self.member_id!r})"
        )
