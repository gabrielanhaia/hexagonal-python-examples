from dataclasses import dataclass
from datetime import UTC, time, timedelta
from fractions import Fraction

from entities.values import Money, TimeSlot

type RoomId = str


@dataclass(frozen=True, slots=True, kw_only=True)
class OpeningHours:
    opens: time  # UTC, to keep the example small
    closes: time

    def contain(self, slot: TimeSlot) -> bool:
        start = slot.start.astimezone(UTC)
        end = slot.end.astimezone(UTC)
        return (
            start.date() == end.date()
            and self.opens <= start.time()
            and end.time() <= self.closes
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Room:
    id: RoomId
    name: str
    hourly_rate: Money
    hours: OpeningHours

    def price_for(self, slot: TimeSlot) -> Money:
        minutes = slot.duration // timedelta(minutes=1)
        return self.hourly_rate.times(Fraction(minutes, 60))
