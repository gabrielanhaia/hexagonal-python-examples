"""Ports the core writes, in its own words."""

from typing import Protocol

from model import Booking, BookingId, Money, PaymentId


class BookingRepository(Protocol):
    async def get(
        self, booking_id: BookingId
    ) -> Booking | None: ...

    async def save(self, booking: Booking) -> None: ...


class PaymentGateway(Protocol):
    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> PaymentId:
        """Capture the amount; raise PaymentDeclined if refused."""
        ...
