from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from fractions import Fraction

from app.domain.errors import IllegalTransition, OutsideOpeningHours
from app.domain.room import Room, RoomId
from app.domain.values import Money, TimeSlot

type BookingId = str
type MemberId = str

HOLD_TTL = timedelta(minutes=15)
FREE_CANCELLATION_NOTICE = timedelta(hours=24)
LATE_CANCELLATION_FEE = Fraction(1, 2)


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


def hold_cutoff(now: datetime) -> datetime:
    """Holds created before this moment have expired."""
    return now - HOLD_TTL


def hold_expired(created_at: datetime, now: datetime) -> bool:
    return created_at < hold_cutoff(now)


def cancellation_fee(
    price: Money, start: datetime, now: datetime
) -> Money:
    if start - now >= FREE_CANCELLATION_NOTICE:
        return price.times(Fraction(0))
    return price.times(LATE_CANCELLATION_FEE)


@dataclass(slots=True, kw_only=True)
class Booking:
    id: BookingId
    room_id: RoomId
    member_id: MemberId
    slot: TimeSlot
    price: Money
    created_at: datetime
    status: BookingStatus = BookingStatus.HELD
    payment_id: str | None = None
    fee: Money | None = None

    @classmethod
    def hold(
        cls,
        *,
        id: BookingId,
        room: Room,
        member_id: MemberId,
        slot: TimeSlot,
        now: datetime,
    ) -> Booking:
        if not room.hours.contain(slot):
            raise OutsideOpeningHours("Room is closed at that time")
        return cls(
            id=id,
            room_id=room.id,
            member_id=member_id,
            slot=slot,
            price=room.price_for(slot),
            created_at=now,
        )

    def is_expired(self, now: datetime) -> bool:
        return self.status is BookingStatus.HELD and hold_expired(
            self.created_at, now
        )

    def blocks_slot(self, now: datetime) -> bool:
        if self.status is BookingStatus.CONFIRMED:
            return True
        return self.status is BookingStatus.HELD and not (
            self.is_expired(now)
        )

    def check_held(self) -> None:
        self._require(BookingStatus.HELD)

    def expire(self) -> None:
        self._require(BookingStatus.HELD)
        self.status = BookingStatus.EXPIRED

    def confirm(self, payment_id: str) -> None:
        self._require(BookingStatus.HELD)
        self.status = BookingStatus.CONFIRMED
        self.payment_id = payment_id

    def cancel(self, now: datetime) -> Money:
        self._require(BookingStatus.HELD, BookingStatus.CONFIRMED)
        self.status = BookingStatus.CANCELLED
        self.fee = cancellation_fee(
            self.price, self.slot.start, now
        )
        return self.fee

    def _require(self, *allowed: BookingStatus) -> None:
        if self.status not in allowed:
            raise IllegalTransition(f"Booking is {self.status}")
