from datetime import datetime
from typing import Protocol

from app.domain.booking import Booking, BookingId
from app.domain.room import Room, RoomId
from app.domain.values import TimeSlot


class RoomRepository(Protocol):
    async def get(self, room_id: RoomId) -> Room | None: ...


class BookingRepository(Protocol):
    async def get(
        self, booking_id: BookingId
    ) -> Booking | None: ...

    async def save(self, booking: Booking) -> None: ...

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        """Held or confirmed bookings of the room over the slot.

        Whether a hold has expired is the domain's call:
        see Booking.blocks_slot.
        """
        ...


class Clock(Protocol):
    def now(self) -> datetime: ...
