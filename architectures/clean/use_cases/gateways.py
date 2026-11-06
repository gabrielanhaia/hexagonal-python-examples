from datetime import datetime
from typing import Protocol

from entities.booking import Booking, BookingId
from entities.room import Room, RoomId
from entities.values import TimeSlot


class RoomGateway(Protocol):
    async def get(self, room_id: RoomId) -> Room | None: ...


class BookingGateway(Protocol):
    async def get(
        self, booking_id: BookingId
    ) -> Booking | None: ...

    async def save(self, booking: Booking) -> None: ...

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        """Active bookings of the room that overlap the slot."""
        ...


class Clock(Protocol):
    def now(self) -> datetime: ...
