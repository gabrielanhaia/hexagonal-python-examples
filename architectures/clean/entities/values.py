import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction

from entities.errors import InvalidTimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class Money:
    amount: int  # minor units: 2400 EUR is 24.00 EUR
    currency: str

    def times(self, factor: Fraction) -> Money:
        return Money(
            amount=math.floor(self.amount * factor),
            currency=self.currency,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class TimeSlot:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise InvalidTimeSlot("start and end need a timezone")
        if self.start >= self.end:
            raise InvalidTimeSlot("start must be before end")
        for moment in (self.start, self.end):
            if (
                moment.minute % 15
                or moment.second
                or moment.microsecond
            ):
                raise InvalidTimeSlot(
                    "slots move in 15-minute steps"
                )

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end
