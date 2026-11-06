from collections.abc import Iterable
from dataclasses import replace

from roombook.booking.domain import (
    Booking,
    BookingStatus,
    Room,
    TimeSlot,
)


class InMemoryRooms:
    def __init__(self, rooms: Iterable[Room]) -> None:
        self._rooms = {room.id: room for room in rooms}

    async def get(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)


class InMemoryBookings:
    def __init__(self) -> None:
        self._rows: dict[str, Booking] = {}

    async def get(self, booking_id: str) -> Booking | None:
        row = self._rows.get(booking_id)
        return None if row is None else replace(row)

    async def save(self, booking: Booking) -> None:
        self._rows[booking.id] = replace(booking)

    async def overlapping(
        self, room_id: str, slot: TimeSlot
    ) -> list[Booking]:
        return [
            replace(row)
            for row in self._rows.values()
            if row.room_id == room_id
            and row.status is BookingStatus.HELD
            and row.slot.overlaps(slot)
        ]
