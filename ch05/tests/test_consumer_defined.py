"""The fakes are a dict and a counter."""

from dataclasses import replace

import httpx2
import pytest

from consumer_defined.confirm import ConfirmBooking
from consumer_defined.tillpoint import TillpointPayments
from model import (
    Booking,
    BookingId,
    BookingStatus,
    Money,
    PaymentDeclined,
    PaymentId,
)

PRICE = Money(amount=2400, currency="EUR")


class InMemoryBookings:
    def __init__(self, *bookings: Booking) -> None:
        self._rows = {b.id: replace(b) for b in bookings}

    async def get(self, booking_id: BookingId) -> Booking | None:
        row = self._rows.get(booking_id)
        return None if row is None else replace(row)

    async def save(self, booking: Booking) -> None:
        self._rows[booking.id] = replace(booking)


class FakePayments:
    def __init__(self) -> None:
        self.charged: list[Money] = []

    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> PaymentId:
        self.charged.append(amount)
        return f"pay-{len(self.charged)}"


async def test_confirm_charges_the_price_once() -> None:
    bookings = InMemoryBookings(Booking(id="b-1", price=PRICE))
    payments = FakePayments()

    await ConfirmBooking(bookings=bookings, payments=payments)(
        "b-1"
    )

    confirmed = await bookings.get("b-1")
    assert confirmed is not None
    assert confirmed.status is BookingStatus.CONFIRMED
    assert payments.charged == [PRICE]


async def test_tillpoint_adapter_turns_a_402_into_a_decline() -> (
    None
):
    client = httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(402)
        ),
        base_url="https://tillpoint.test",
    )
    async with client:
        with pytest.raises(PaymentDeclined):
            await TillpointPayments(client).charge("b-1", PRICE)
