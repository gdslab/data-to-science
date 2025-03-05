import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base
from app.schemas.team_member import Role


if TYPE_CHECKING:
    from .team import Team
    from .user import User


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[Role] = mapped_column(
        ENUM(Role, name="member_role"), nullable=False, default=Role.MEMBER
    )
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    member: Mapped["User"] = relationship(back_populates="team_memberships")
    team: Mapped["Team"] = relationship(back_populates="members")

    __table_args__ = (UniqueConstraint("member_id", "team_id", name="unique_to_team"),)

    def __repr__(self) -> str:
        return (
            f"TeamMember(id={self.id!r}, role={self.role}, "
            f"member_id={self.member_id!r}, team_id={self.team_id})"
        )
