import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow
from app.schemas.job import State, Status


if TYPE_CHECKING:
    from .data_product import DataProduct
    from .raw_data import RawData


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    extra: Mapped[dict] = mapped_column(JSONB, nullable=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    state: Mapped[State] = mapped_column(ENUM(State, name="job_state"), nullable=False)
    status: Mapped[Status] = mapped_column(
        ENUM(Status, name="job_status", nullable=False)
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=True
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=True
    )

    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=True
    )
    raw_data_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_data.id"), nullable=True
    )

    data_product: Mapped["DataProduct"] = relationship(back_populates="jobs")
    raw_data: Mapped["RawData"] = relationship(back_populates="jobs")

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id!r}, extra={self.extra!r}, name={self.name!r}, "
            f"state={self.state!r}, status={self.status!r}, "
            f"start_time={self.start_time!r}, end_time={self.end_time!r}, "
            f"data_product_id={self.data_product_id!r}, "
            f"raw_data_id={self.raw_data_id!r})"
        )
