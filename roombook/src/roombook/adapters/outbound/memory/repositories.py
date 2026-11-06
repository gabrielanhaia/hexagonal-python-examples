"""Repositories over dictionaries, with database semantics."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime

from roombook.domain.booking import (
    ACTIVE_STATUSES,
    Booking,
    BookingStatus,
)
from roombook.domain.errors import SlotUnavailable
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId, RoomId
from roombook.domain.room import Room
from roombook.domain.time_slot import TimeSlot


class InMemoryBookingRepository:
    """Stores copies, so an unsaved change is never persisted."""

    def __init__(self, rows: dict[BookingId, Booking]) -> None:
        self.rows = rows

    async def add(self, booking: Booking) -> None:
        if await self.overlapping(booking.room_id, booking.slot):
            raise SlotUnavailable(
                f"room {booking.room_id} is already booked "
                f"for {booking.slot}"
            )
        self.rows[booking.id] = replace(booking)

    async def get(self, booking_id: BookingId) -> Booking | None:
        row = self.rows.get(booking_id)
        return None if row is None else replace(row)

    async def save(self, booking: Booking) -> None:
        self.rows[booking.id] = replace(booking)

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        return [
            replace(row)
            for row in self.rows.values()
            if row.room_id == room_id
            and row.status in ACTIVE_STATUSES
            and row.slot.overlaps(slot)
        ]

    async def stale_holds(self, now: datetime) -> list[Booking]:
        return [
            replace(row)
            for row in self.rows.values()
            if row.status is BookingStatus.HELD
            and row.expires_at <= now
        ]


class InMemoryRoomRepository:
    def __init__(self, rooms: dict[RoomId, Room]) -> None:
        self._rooms = rooms

    async def get(self, room_id: RoomId) -> Room | None:
        return self._rooms.get(room_id)


class InMemoryOutbox:
    def __init__(self) -> None:
        self.pending: list[BookingEvent] = []

    async def put(self, events: Sequence[BookingEvent]) -> None:
        self.pending.extend(events)
