from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Booking(Base):
    """The domain entity and the ORM model in one class."""

    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(36))
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(String(20), default="HELD")

    def overlaps(self, other: Booking) -> bool:
        return (
            self.room_id == other.room_id
            and self.starts_at < other.ends_at
            and other.starts_at < self.ends_at
        )
