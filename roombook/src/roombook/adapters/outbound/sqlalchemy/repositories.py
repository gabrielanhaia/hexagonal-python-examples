"""Repositories over an AsyncSession. Records never leak out."""

from collections.abc import Sequence
from datetime import datetime

from psycopg.errors import ExclusionViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from roombook.adapters.outbound.outbox.messages import to_message
from roombook.adapters.outbound.sqlalchemy.mappers import (
    booking_from_record,
    booking_to_record,
    room_from_record,
    slot_to_range,
    update_record,
)
from roombook.adapters.outbound.sqlalchemy.records import (
    BookingRecord,
    OutboxRecord,
    RoomRecord,
)
from roombook.domain.booking import (
    ACTIVE_STATUSES,
    HOLD_DURATION,
    Booking,
    BookingStatus,
)
from roombook.domain.errors import SlotUnavailable
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId, RoomId
from roombook.domain.room import Room
from roombook.domain.time_slot import TimeSlot


class SqlAlchemyBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, booking: Booking) -> None:
        self._session.add(booking_to_record(booking))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if isinstance(error.orig, ExclusionViolation):
                raise SlotUnavailable(
                    f"room {booking.room_id} is already booked "
                    f"for {booking.slot}"
                ) from error
            raise

    async def get(self, booking_id: BookingId) -> Booking | None:
        record = await self._session.get(
            BookingRecord, booking_id, with_for_update=True
        )
        return (
            None if record is None else booking_from_record(record)
        )

    async def save(self, booking: Booking) -> None:
        record = await self._session.get_one(
            BookingRecord, booking.id
        )
        update_record(record, booking)

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        statement = select(BookingRecord).where(
            BookingRecord.room_id == room_id,
            BookingRecord.status.in_(ACTIVE_STATUSES),
            BookingRecord.slot.overlaps(slot_to_range(slot)),
        )
        records = await self._session.scalars(statement)
        return [booking_from_record(record) for record in records]

    async def stale_holds(self, now: datetime) -> list[Booking]:
        statement = (
            select(BookingRecord)
            .where(
                BookingRecord.status == BookingStatus.HELD,
                BookingRecord.held_at <= now - HOLD_DURATION,
            )
            .with_for_update(skip_locked=True)
        )
        records = await self._session.scalars(statement)
        return [booking_from_record(record) for record in records]


class SqlAlchemyRoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, room_id: RoomId) -> Room | None:
        record = await self._session.get(RoomRecord, room_id)
        return None if record is None else room_from_record(record)


class SqlAlchemyOutbox:
    """Writes events in the same transaction as the booking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def put(self, events: Sequence[BookingEvent]) -> None:
        for event in events:
            message = to_message(event)
            self._session.add(
                OutboxRecord(
                    topic=message.topic,
                    key=message.key,
                    type=message.type,
                    payload=message.payload,
                    occurred_at=message.occurred_at,
                )
            )
