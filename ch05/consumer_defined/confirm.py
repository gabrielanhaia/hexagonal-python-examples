from consumer_defined.ports import BookingRepository, PaymentGateway
from model import BookingId, BookingNotFound, IllegalTransition


class ConfirmBooking:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        payments: PaymentGateway,
    ) -> None:
        self._bookings = bookings
        self._payments = payments

    async def __call__(self, booking_id: BookingId) -> None:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFound(booking_id)
        if not booking.can_confirm:
            raise IllegalTransition(f"booking is {booking.status}")
        payment_id = await self._payments.charge(
            booking.id, booking.price
        )
        booking.confirm(payment_id)
        await self._bookings.save(booking)
