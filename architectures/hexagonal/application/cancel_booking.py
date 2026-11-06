from dataclasses import dataclass

from application.ports import BookingRepository, Clock
from domain.booking import Booking, BookingId
from domain.errors import BookingNotFound
from domain.values import Money


@dataclass(frozen=True, slots=True, kw_only=True)
class Cancellation:
    booking: Booking
    fee: Money


class CancelBooking:
    def __init__(
        self, *, bookings: BookingRepository, clock: Clock
    ) -> None:
        self._bookings = bookings
        self._clock = clock

    async def __call__(self, booking_id: BookingId) -> Cancellation:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFound(booking_id)
        fee = booking.cancel(now=self._clock.now())
        await self._bookings.save(booking)
        return Cancellation(booking=booking, fee=fee)
