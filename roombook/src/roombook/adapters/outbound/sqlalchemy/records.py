"""ORM records: the shape of the tables, not of the domain."""

from datetime import datetime, time
from typing import Any, ClassVar

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    TSTZRANGE,
    ExcludeConstraint,
    Range,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        str: Text,
        datetime: DateTime(timezone=True),
    }


class RoomRecord(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    capacity: Mapped[int]
    hourly_rate: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))
    opens: Mapped[time]
    closes: Mapped[time]
    timezone: Mapped[str]


class BookingRecord(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        ExcludeConstraint(
            ("room_id", "="),
            ("slot", "&&"),
            name="bookings_no_overlap",
            using="gist",
            where=text("status IN ('HELD', 'CONFIRMED')"),
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True
    )
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))
    member_id: Mapped[str]
    slot: Mapped[Range[datetime]] = mapped_column(TSTZRANGE)
    price: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(16))
    held_at: Mapped[datetime]
    payment_id: Mapped[str | None]


class OutboxRecord(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    topic: Mapped[str]
    key: Mapped[str]
    type: Mapped[str]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    occurred_at: Mapped[datetime]
    published_at: Mapped[datetime | None]


class ProcessedMessageRecord(Base):
    __tablename__ = "processed_messages"

    message_id: Mapped[str] = mapped_column(primary_key=True)
    processed_at: Mapped[datetime]
