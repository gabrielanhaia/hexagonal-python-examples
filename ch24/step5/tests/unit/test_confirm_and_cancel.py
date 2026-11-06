"""ConfirmBooking and CancelBooking with fakes: no I/O at all."""

from datetime import UTC, datetime, time, timedelta

import pytest

from app.adapters.memory import InMemoryBookingRepository
from app.application.cancel_booking import CancelBooking
from app.application.confirm_booking import ConfirmBooking
from app.domain.booking import Booking, BookingId, BookingStatus
from app.domain.errors import HoldExpired, PaymentDeclined
from app.domain.room import OpeningHours, Room
from app.domain.values import Money, TimeSlot

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
PRICE = Money(amount=2400, currency="EUR")
ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=PRICE,
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakePayments:
    def __init__(self, *, declines: bool = False) -> None:
        self.declines = declines
        self.charged: list[Money] = []

    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> str:
        if self.declines:
            raise PaymentDeclined("Payment declined")
        self.charged.append(amount)
        return "pay-1"


async def stored_hold(
    bookings: InMemoryBookingRepository, day: int = 10
) -> Booking:
    booking = Booking.hold(
        id="b-1",
        room=ATLAS,
        member_id="m-1",
        slot=TimeSlot(
            start=datetime(2026, 11, day, 10, tzinfo=UTC),
            end=datetime(2026, 11, day, 11, tzinfo=UTC),
        ),
        now=NOW,
    )
    await bookings.save(booking)
    return booking


async def test_confirm_charges_the_price() -> None:
    bookings, payments = InMemoryBookingRepository(), FakePayments()
    await stored_hold(bookings)
    confirm = ConfirmBooking(
        bookings=bookings, payments=payments, clock=FixedClock(NOW)
    )

    booking = await confirm("b-1")

    assert booking.status is BookingStatus.CONFIRMED
    assert payments.charged == [PRICE]


async def test_an_expired_hold_is_expired_and_not_charged() -> None:
    bookings, payments = InMemoryBookingRepository(), FakePayments()
    await stored_hold(bookings)
    later = FixedClock(NOW + timedelta(minutes=16))
    confirm = ConfirmBooking(
        bookings=bookings, payments=payments, clock=later
    )

    with pytest.raises(HoldExpired):
        await confirm("b-1")

    stored = await bookings.get("b-1")
    assert stored is not None
    assert stored.status is BookingStatus.EXPIRED
    assert payments.charged == []


async def test_a_declined_payment_keeps_the_hold() -> None:
    bookings = InMemoryBookingRepository()
    await stored_hold(bookings)
    confirm = ConfirmBooking(
        bookings=bookings,
        payments=FakePayments(declines=True),
        clock=FixedClock(NOW),
    )

    with pytest.raises(PaymentDeclined):
        await confirm("b-1")

    stored = await bookings.get("b-1")
    assert stored is not None
    assert stored.status is BookingStatus.HELD


async def test_cancelling_late_costs_half() -> None:
    bookings = InMemoryBookingRepository()
    await stored_hold(bookings, day=9)
    cancel = CancelBooking(bookings=bookings, clock=FixedClock(NOW))

    cancellation = await cancel("b-1")

    assert cancellation.fee == Money(amount=1200, currency="EUR")
