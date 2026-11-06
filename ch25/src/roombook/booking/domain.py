import math
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum
from fractions import Fraction

FREE_CANCELLATION_NOTICE = timedelta(hours=24)
LATE_CANCELLATION_FEE = Fraction(1, 2)


class BookingError(Exception):
    pass


class InvalidBooking(BookingError):
    pass


class SlotUnavailable(BookingError):
    pass


class IllegalTransition(BookingError):
    pass


class NotFound(BookingError):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class Money:
    amount: int  # minor units
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
        if self.start.tzinfo is None or self.start >= self.end:
            raise InvalidBooking("need an aware start before end")
        for moment in (self.start, self.end):
            if moment.minute % 15 or moment.second:
                raise InvalidBooking(
                    "slots move in 15-minute steps"
                )

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True, slots=True, kw_only=True)
class Room:
    id: str
    hourly_rate: Money
    opens: time  # UTC
    closes: time

    def price_for(self, slot: TimeSlot) -> Money:
        start, end = (
            slot.start.astimezone(UTC),
            slot.end.astimezone(UTC),
        )
        if not (
            start.date() == end.date()
            and self.opens <= start.time()
            and end.time() <= self.closes
        ):
            raise InvalidBooking("the room is closed then")
        minutes = (end - start) // timedelta(minutes=1)
        return self.hourly_rate.times(Fraction(minutes, 60))


class BookingStatus(StrEnum):
    HELD = "HELD"
    CANCELLED = "CANCELLED"


@dataclass(slots=True, kw_only=True)
class Booking:
    id: str
    room_id: str
    member_id: str
    slot: TimeSlot
    price: Money
    status: BookingStatus = BookingStatus.HELD

    def cancel(self, now: datetime) -> Money:
        if self.status is not BookingStatus.HELD:
            raise IllegalTransition(f"booking is {self.status}")
        self.status = BookingStatus.CANCELLED
        if self.slot.start - now >= FREE_CANCELLATION_NOTICE:
            return self.price.times(Fraction(0))
        return self.price.times(LATE_CANCELLATION_FEE)
