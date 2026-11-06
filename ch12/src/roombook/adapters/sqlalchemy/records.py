"""ORM records: one row per room, one row per blackout."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Dialect, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """SQLite drops the offset: store UTC, read it back aware."""

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


class RoomRecord(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    blackouts: Mapped[list[BlackoutRecord]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class BlackoutRecord(Base):
    __tablename__ = "blackouts"

    id: Mapped[str] = mapped_column(primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))
    starts_at: Mapped[datetime] = mapped_column(UtcDateTime)
    ends_at: Mapped[datetime] = mapped_column(UtcDateTime)
    reason: Mapped[str]
    room: Mapped[RoomRecord] = relationship(
        back_populates="blackouts"
    )
