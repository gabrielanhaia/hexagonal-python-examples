"""Rooms, their prices and the hours they can be booked."""

from dataclasses import dataclass
from datetime import date, datetime, time
from fractions import Fraction
from zoneinfo import ZoneInfo

from roombook.domain.errors import OutsideOpeningHours
from roombook.domain.ids import RoomId
from roombook.domain.money import Money
from roombook.domain.time_slot import GRANULARITY, TimeSlot

_QUARTERS_PER_HOUR = 4


@dataclass(frozen=True, slots=True, kw_only=True)
class OpeningHours:
    opens: time
    closes: time
    timezone: str

    def __post_init__(self) -> None:
        if self.opens >= self.closes:
            raise ValueError("a room must open before it closes")

    def on(self, day: date) -> TimeSlot:
        """The open window on one local calendar day."""
        zone = ZoneInfo(self.timezone)
        return TimeSlot(
            datetime.combine(day, self.opens, tzinfo=zone),
            datetime.combine(day, self.closes, tzinfo=zone),
        )

    def local_day(self, moment: datetime) -> date:
        return moment.astimezone(ZoneInfo(self.timezone)).date()


@dataclass(frozen=True, slots=True, kw_only=True)
class Room:
    id: RoomId
    name: str
    capacity: int
    hourly_rate: Money
    opening_hours: OpeningHours

    def check_open(self, slot: TimeSlot) -> None:
        hours = self.opening_hours
        window = hours.on(hours.local_day(slot.start))
        if not window.contains(slot):
            raise OutsideOpeningHours(
                f"{self.name} is open {hours.opens:%H:%M}-"
                f"{hours.closes:%H:%M} ({hours.timezone})"
            )

    def price_for(self, slot: TimeSlot) -> Money:
        quarters = slot.duration // GRANULARITY
        share = Fraction(quarters, _QUARTERS_PER_HOUR)
        return self.hourly_rate.scaled(share)
