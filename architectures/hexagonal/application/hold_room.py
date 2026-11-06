from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from application.ports import BookingRepository, RoomRepository
from domain.booking import Booking, MemberId
from domain.errors import RoomNotFound, SlotUnavailable
from domain.room import RoomId
from domain.values import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomCommand:
    room_id: RoomId
    member_id: MemberId
    start: datetime
    end: datetime


class HoldRoom:
    def __init__(
        self, *, rooms: RoomRepository, bookings: BookingRepository
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings

    async def __call__(self, command: HoldRoomCommand) -> Booking:
        slot = TimeSlot(start=command.start, end=command.end)
        room = await self._rooms.get(command.room_id)
        if room is None:
            raise RoomNotFound(command.room_id)
        booking = Booking.hold(
            id=uuid4().hex,
            room=room,
            member_id=command.member_id,
            slot=slot,
        )
        if await self._bookings.overlapping(room.id, slot):
            raise SlotUnavailable(f"{room.name} is taken then")
        await self._bookings.save(booking)
        return booking
