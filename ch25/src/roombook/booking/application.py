from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from roombook.booking.domain import (
    Booking,
    Money,
    NotFound,
    Room,
    SlotUnavailable,
    TimeSlot,
)
from roombook.contracts.events import BookingCancelled


class Rooms(Protocol):
    async def get(self, room_id: str) -> Room | None: ...


class Bookings(Protocol):
    async def get(self, booking_id: str) -> Booking | None: ...

    async def save(self, booking: Booking) -> None: ...

    async def overlapping(
        self, room_id: str, slot: TimeSlot
    ) -> list[Booking]: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class Events(Protocol):
    async def publish(self, event: BookingCancelled) -> None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomCommand:
    room_id: str
    member_id: str
    start: datetime
    end: datetime


class HoldRoom:
    def __init__(self, *, rooms: Rooms, bookings: Bookings) -> None:
        self._rooms = rooms
        self._bookings = bookings

    async def __call__(self, command: HoldRoomCommand) -> Booking:
        slot = TimeSlot(start=command.start, end=command.end)
        room = await self._rooms.get(command.room_id)
        if room is None:
            raise NotFound(f"no room {command.room_id}")
        booking = Booking(
            id=uuid4().hex,
            room_id=room.id,
            member_id=command.member_id,
            slot=slot,
            price=room.price_for(slot),
        )
        if await self._bookings.overlapping(room.id, slot):
            raise SlotUnavailable("the room is taken then")
        await self._bookings.save(booking)
        return booking


class CancelBooking:
    def __init__(
        self, *, bookings: Bookings, clock: Clock, events: Events
    ) -> None:
        self._bookings = bookings
        self._clock = clock
        self._events = events

    async def __call__(self, booking_id: str) -> Money:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise NotFound(f"no booking {booking_id}")
        now = self._clock.now()
        fee = booking.cancel(now)
        await self._bookings.save(booking)
        await self._events.publish(
            BookingCancelled(
                booking_id=booking.id,
                member_id=booking.member_id,
                fee_amount=fee.amount,
                currency=fee.currency,
                occurred_at=now,
            )
        )
        return fee
