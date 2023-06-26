from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight


class RawData(Base):
    __tablename__ = "raw_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_path: Mapped[str] = mapped_column(String, nullable=False)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False)    

    flight: Mapped["Flight"] = relationship(back_populates="raw_data")
