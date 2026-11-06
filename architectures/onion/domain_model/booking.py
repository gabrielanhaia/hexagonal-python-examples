from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from fractions import Fraction

from domain_model.errors import (
    IllegalTransition,
    OutsideOpeningHours,
)
from domain_model.room import Room, RoomId
from domain_model.values import Money, TimeSlot

type BookingId = str
type MemberId = str

FREE_CANCELLATION_NOTICE = timedelta(hours=24)
LATE_CANCELLATION_FEE = Fraction(1, 2)


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


ACTIVE = frozenset({BookingStatus.HELD, BookingStatus.CONFIRMED})


@dataclass(slots=True, kw_only=True)
class Booking:
    id: BookingId
    room_id: RoomId
    member_id: MemberId
    slot: TimeSlot
    price: Money
    status: BookingStatus = BookingStatus.HELD

    @classmethod
    def hold(
        cls,
        *,
        id: BookingId,
        room: Room,
        member_id: MemberId,
        slot: TimeSlot,
    ) -> Booking:
        if not room.hours.contain(slot):
            raise OutsideOpeningHours(f"{room.name} is closed then")
        return cls(
            id=id,
            room_id=room.id,
            member_id=member_id,
            slot=slot,
            price=room.price_for(slot),
        )

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE

    def cancel(self, *, now: datetime) -> Money:
        if not self.is_active:
            raise IllegalTransition(f"booking is {self.status}")
        self.status = BookingStatus.CANCELLED
        return cancellation_fee(self.price, self.slot.start, now)


def cancellation_fee(
    price: Money, start: datetime, now: datetime
) -> Money:
    if start - now >= FREE_CANCELLATION_NOTICE:
        return price.times(Fraction(0))
    return price.times(LATE_CANCELLATION_FEE)
