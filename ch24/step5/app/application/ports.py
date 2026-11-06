from datetime import datetime
from typing import Protocol

from app.domain.booking import Booking, BookingId
from app.domain.room import Room, RoomId
from app.domain.values import Money, TimeSlot


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


class PaymentGateway(Protocol):
    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> str:
        """Capture the amount and return the payment id.

        Raises PaymentDeclined when the provider refuses.
        """
        ...
