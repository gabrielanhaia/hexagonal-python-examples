from datetime import UTC, datetime, time
from uuid import uuid4

from sqlalchemy import DateTime, Dialect, ForeignKey, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
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


class RoomRow(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    capacity: Mapped[int]
    hourly_rate_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))
    opens_at: Mapped[time]  # UTC
    closes_at: Mapped[time]  # UTC

    bookings: Mapped[list[BookingRow]] = relationship(
        back_populates="room"
    )


class BookingRow(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))
    member_id: Mapped[str] = mapped_column(String(36))
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(20), default="HELD")
    price_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))
    payment_id: Mapped[str | None] = mapped_column(String(64))
    cancellation_fee_cents: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(UTC)
    )

    room: Mapped[RoomRow] = relationship(back_populates="bookings")
