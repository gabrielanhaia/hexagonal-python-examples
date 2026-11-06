from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from application_services.clock import Clock
from domain_model.booking import Booking, BookingId, MemberId
from domain_model.errors import BookingNotFound, RoomNotFound
from domain_model.room import RoomId
from domain_model.values import Money, TimeSlot
from domain_services.availability import AvailabilityService
from domain_services.repositories import (
    BookingRepository,
    RoomRepository,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Cancellation:
    booking: Booking
    fee: Money


class BookingApplicationService:
    def __init__(
        self,
        *,
        rooms: RoomRepository,
        bookings: BookingRepository,
        availability: AvailabilityService,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._availability = availability
        self._clock = clock

    async def hold_room(
        self,
        *,
        room_id: RoomId,
        member_id: MemberId,
        start: datetime,
        end: datetime,
    ) -> Booking:
        slot = TimeSlot(start=start, end=end)
        room = await self._rooms.get(room_id)
        if room is None:
            raise RoomNotFound(room_id)
        booking = Booking.hold(
            id=uuid4().hex,
            room=room,
            member_id=member_id,
            slot=slot,
        )
        await self._availability.ensure_free(room, slot)
        await self._bookings.save(booking)
        return booking

    async def cancel_booking(
        self, booking_id: BookingId
    ) -> Cancellation:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFound(booking_id)
        fee = booking.cancel(now=self._clock.now())
        await self._bookings.save(booking)
        return Cancellation(booking=booking, fee=fee)
