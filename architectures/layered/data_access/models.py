from datetime import UTC, datetime, time
from enum import StrEnum

from sqlalchemy import DateTime, Dialect, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Stores aware datetimes as naive UTC; SQLite has no zones."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


ACTIVE = (BookingStatus.HELD, BookingStatus.CONFIRMED)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    hourly_rate: Mapped[int]  # minor units
    currency: Mapped[str] = mapped_column(String(3))
    opens: Mapped[time]  # UTC
    closes: Mapped[time]


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))
    member_id: Mapped[str]
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime)
    price: Mapped[int]  # minor units
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[BookingStatus]
