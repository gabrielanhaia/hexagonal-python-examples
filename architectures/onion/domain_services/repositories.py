from typing import Protocol

from domain_model.booking import Booking, BookingId
from domain_model.room import Room, RoomId
from domain_model.values import TimeSlot


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
        """Active bookings of the room that overlap the slot."""
        ...
