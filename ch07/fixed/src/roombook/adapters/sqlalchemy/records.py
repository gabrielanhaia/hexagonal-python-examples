from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from roombook.domain.booking import Booking, BookingStatus


class Base(DeclarativeBase):
    pass


class BookingRecord(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(36))
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(String(20))


def to_domain(record: BookingRecord) -> Booking:
    return Booking(
        id=record.id,
        room_id=record.room_id,
        starts_at=record.starts_at,
        ends_at=record.ends_at,
        status=BookingStatus(record.status),
    )


def to_record(booking: Booking) -> BookingRecord:
    return BookingRecord(
        id=booking.id,
        room_id=booking.room_id,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
        status=booking.status.value,
    )
