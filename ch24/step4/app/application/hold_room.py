from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.application.ports import (
    BookingRepository,
    Clock,
    RoomRepository,
)
from app.domain.booking import Booking, MemberId
from app.domain.errors import RoomNotFound, SlotUnavailable
from app.domain.room import RoomId
from app.domain.values import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomCommand:
    room_id: RoomId
    member_id: MemberId
    start: datetime
    end: datetime


class HoldRoom:
    def __init__(
        self,
        *,
        rooms: RoomRepository,
        bookings: BookingRepository,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._clock = clock

    async def __call__(self, command: HoldRoomCommand) -> Booking:
        room = await self._rooms.get(command.room_id)
        if room is None:
            raise RoomNotFound("Room not found")
        slot = TimeSlot(start=command.start, end=command.end)
        now = self._clock.now()
        booking = Booking.hold(
            id=str(uuid4()),
            room=room,
            member_id=command.member_id,
            slot=slot,
            now=now,
        )
        others = await self._bookings.overlapping(room.id, slot)
        if any(other.blocks_slot(now) for other in others):
            raise SlotUnavailable("Room is already booked")
        await self._bookings.save(booking)
        return booking
