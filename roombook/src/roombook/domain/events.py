"""Domain events: facts the Booking aggregate records."""

from dataclasses import dataclass
from datetime import datetime

from roombook.domain.ids import BookingId, MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.time_slot import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingHeld:
    booking_id: BookingId
    room_id: RoomId
    member_id: MemberId
    slot: TimeSlot
    price: Money
    expires_at: datetime
    occurred_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingConfirmed:
    booking_id: BookingId
    member_id: MemberId
    payment_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingCancelled:
    booking_id: BookingId
    member_id: MemberId
    fee: Money
    refund: Money
    occurred_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldExpired:
    booking_id: BookingId
    member_id: MemberId
    occurred_at: datetime


type BookingEvent = (
    BookingHeld | BookingConfirmed | BookingCancelled | HoldExpired
)
