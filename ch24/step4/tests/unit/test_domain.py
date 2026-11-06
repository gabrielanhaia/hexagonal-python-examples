"""The rules on their own: no database, no HTTP, no clock."""

from datetime import UTC, datetime, time, timedelta

import pytest

from app.domain.booking import cancellation_fee, hold_expired
from app.domain.errors import InvalidTimeSlot
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


def slot(start: int, end: int, day: int = 10) -> TimeSlot:
    return TimeSlot(
        start=datetime(2026, 11, day, start, tzinfo=UTC),
        end=datetime(2026, 11, day, end, tzinfo=UTC),
    )


def test_a_slot_must_start_before_it_ends() -> None:
    with pytest.raises(InvalidTimeSlot):
        slot(11, 10)


def test_a_room_prices_by_the_hour() -> None:
    assert ATLAS.price_for(slot(10, 13)).amount == 7200


def test_opening_hours_contain_the_whole_slot() -> None:
    assert ATLAS.hours.contain(slot(8, 20))
    assert not ATLAS.hours.contain(slot(19, 21))


def test_a_hold_expires_after_15_minutes() -> None:
    assert not hold_expired(NOW - timedelta(minutes=15), NOW)
    assert hold_expired(NOW - timedelta(minutes=16), NOW)


def test_cancellation_is_free_24_hours_ahead() -> None:
    start = NOW + timedelta(hours=24)

    assert cancellation_fee(PRICE, start, NOW).amount == 0
    assert cancellation_fee(
        PRICE, start, NOW + timedelta(minutes=1)
    ) == (Money(amount=1200, currency="EUR"))
