from domain_model.errors import SlotUnavailable
from domain_model.room import Room
from domain_model.values import TimeSlot
from domain_services.repositories import BookingRepository


class AvailabilityService:
    """A rule about many bookings, so it fits no single entity."""

    def __init__(self, bookings: BookingRepository) -> None:
        self._bookings = bookings

    async def ensure_free(self, room: Room, slot: TimeSlot) -> None:
        if await self._bookings.overlapping(room.id, slot):
            raise SlotUnavailable(f"{room.name} is taken then")
