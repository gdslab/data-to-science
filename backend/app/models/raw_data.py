import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight


class RawData(Base):
    __tablename__ = "raw_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_path: Mapped[str] = mapped_column(String, nullable=False)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False)    

    flight: Mapped["Flight"] = relationship(back_populates="raw_data")
