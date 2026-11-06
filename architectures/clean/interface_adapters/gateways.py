from collections.abc import Iterable
from dataclasses import replace

from entities.booking import Booking, BookingId
from entities.room import Room, RoomId
from entities.values import TimeSlot


class InMemoryRoomGateway:
    def __init__(self, rooms: Iterable[Room] = ()) -> None:
        self._rooms = {room.id: room for room in rooms}

    async def get(self, room_id: RoomId) -> Room | None:
        return self._rooms.get(room_id)


class InMemoryBookingGateway:
    def __init__(self) -> None:
        self._bookings: dict[BookingId, Booking] = {}

    async def get(self, booking_id: BookingId) -> Booking | None:
        booking = self._bookings.get(booking_id)
        return None if booking is None else replace(booking)

    async def save(self, booking: Booking) -> None:
        self._bookings[booking.id] = replace(booking)

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        return [
            replace(booking)
            for booking in self._bookings.values()
            if booking.room_id == room_id
            and booking.is_active
            and booking.slot.overlaps(slot)
        ]
