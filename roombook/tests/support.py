"""Test data shared by every layer of the suite."""

from datetime import UTC, datetime, time

from roombook.domain.ids import MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.room import OpeningHours, Room
from roombook.domain.time_slot import TimeSlot

# Lisbon keeps UTC in December, so local and UTC hours agree.
DAY = "2026-12-01"
NOW = datetime(2026, 11, 30, 9, 0, tzinfo=UTC)
ADA = MemberId("member-ada")
GRACE = MemberId("member-grace")


def at(clock_time: str, day: str = DAY) -> datetime:
    """`at("10:30")` is 10:30 UTC on DAY."""
    return datetime.fromisoformat(f"{day}T{clock_time}+00:00")


def slot(start: str, end: str, day: str = DAY) -> TimeSlot:
    return TimeSlot(at(start, day), at(end, day))


def atlas() -> Room:
    return Room(
        id=RoomId("atlas"),
        name="Atlas",
        capacity=8,
        hourly_rate=Money(4000, "EUR"),
        opening_hours=OpeningHours(
            opens=time(8, 0),
            closes=time(20, 0),
            timezone="Europe/Lisbon",
        ),
    )
