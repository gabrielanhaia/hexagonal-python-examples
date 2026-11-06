from app.application.ports import (
    BookingRepository,
    Clock,
    PaymentGateway,
)
from app.domain.booking import Booking, BookingId
from app.domain.errors import BookingNotFound, HoldExpired


class ConfirmBooking:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        payments: PaymentGateway,
        clock: Clock,
    ) -> None:
        self._bookings = bookings
        self._payments = payments
        self._clock = clock

    async def __call__(self, booking_id: BookingId) -> Booking:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFound("Booking not found")
        booking.check_held()
        if booking.is_expired(self._clock.now()):
            booking.expire()
            await self._bookings.save(booking)
            raise HoldExpired("Hold expired")
        payment_id = await self._payments.charge(
            booking.id, booking.price
        )
        booking.confirm(payment_id)
        await self._bookings.save(booking)
        return booking
