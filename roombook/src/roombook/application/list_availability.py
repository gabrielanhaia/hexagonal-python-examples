"""List the free time in a room on one day."""

from dataclasses import dataclass
from datetime import date

from roombook.application.ports import UnitOfWorkFactory
from roombook.domain.availability import free_slots
from roombook.domain.errors import RoomNotFound
from roombook.domain.ids import RoomId
from roombook.domain.time_slot import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class AvailabilityQuery:
    room_id: RoomId
    day: date


@dataclass(frozen=True, slots=True, kw_only=True)
class Availability:
    room_id: RoomId
    day: date
    free: tuple[TimeSlot, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ListAvailability:
    unit_of_work: UnitOfWorkFactory

    async def __call__(
        self, query: AvailabilityQuery
    ) -> Availability:
        async with self.unit_of_work() as uow:
            room = await uow.rooms.get(query.room_id)
            if room is None:
                raise RoomNotFound(f"no room {query.room_id}")
            window = room.opening_hours.on(query.day)
            taken = await uow.bookings.overlapping(room.id, window)
        free = free_slots(
            window, [booking.slot for booking in taken]
        )
        return Availability(
            room_id=room.id, day=query.day, free=tuple(free)
        )
