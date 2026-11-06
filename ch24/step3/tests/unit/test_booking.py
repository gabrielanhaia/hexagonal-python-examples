from datetime import UTC, datetime, time, timedelta

import pytest

from app.domain.booking import Booking, BookingStatus
from app.domain.errors import IllegalTransition, OutsideOpeningHours
from app.domain.room import OpeningHours, Room
from app.domain.values import Money, TimeSlot

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


def held(start: int = 10, end: int = 11) -> Booking:
    return Booking.hold(
        id="b-1",
        room=ATLAS,
        member_id="m-1",
        slot=TimeSlot(
            start=datetime(2026, 11, 10, start, tzinfo=UTC),
            end=datetime(2026, 11, 10, end, tzinfo=UTC),
        ),
        now=NOW,
    )


def test_a_hold_is_priced_and_blocks_its_slot() -> None:
    booking = held()

    assert booking.price == Money(amount=2400, currency="EUR")
    assert booking.blocks_slot(NOW)


def test_an_expired_hold_stops_blocking() -> None:
    assert not held().blocks_slot(NOW + timedelta(minutes=16))


def test_a_hold_must_fit_the_opening_hours() -> None:
    with pytest.raises(OutsideOpeningHours):
        held(19, 21)


def test_a_cancelled_booking_cannot_be_cancelled_again() -> None:
    booking = held()
    booking.cancel(NOW)

    assert booking.status is BookingStatus.CANCELLED
    with pytest.raises(IllegalTransition, match="CANCELLED"):
        booking.cancel(NOW)
