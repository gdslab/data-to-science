import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

JOB_STATE = ["PENDING", "STARTED", "COMPLETED"]
JOB_STATUS = ["WAITING", "INPROGRESS", "SUCCESS", "FAILED"]


if TYPE_CHECKING:
    from .data_product import DataProduct
    from .raw_data import RawData


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    state: Mapped[enumerate] = mapped_column(
        ENUM(*JOB_STATE, name="job_state"), nullable=False
    )
    status: Mapped[enumerate] = mapped_column(
        ENUM(*JOB_STATUS, name="job_status", nullable=False)
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

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
            f"Job(id={self.id!r}, name={self.name!r}, state={self.state!r}, "
            f"status={self.status!r}, start_time={self.start_time!r}, "
            f"end_time={self.end_time!r})"
        )
