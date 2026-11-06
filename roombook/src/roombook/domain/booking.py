"""The Booking aggregate: one member's claim on one slot."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from roombook.domain.cancellation import (
    CancellationTerms,
    cancellation_terms,
)
from roombook.domain.errors import (
    IllegalTransition,
    InvalidTimeSlot,
)
from roombook.domain.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingEvent,
    BookingHeld,
    HoldExpired,
)
from roombook.domain.ids import BookingId, MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.room import Room
from roombook.domain.time_slot import TimeSlot

HOLD_DURATION = timedelta(minutes=15)


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


ACTIVE_STATUSES = frozenset(
    {BookingStatus.HELD, BookingStatus.CONFIRMED}
)

_NEXT: dict[BookingStatus, frozenset[BookingStatus]] = {
    BookingStatus.HELD: frozenset(
        {
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
            BookingStatus.EXPIRED,
        }
    ),
    BookingStatus.CONFIRMED: frozenset({BookingStatus.CANCELLED}),
    BookingStatus.CANCELLED: frozenset(),
    BookingStatus.EXPIRED: frozenset(),
}


@dataclass(kw_only=True, eq=False)
class Booking:
    """Aggregate root. Equal to another Booking by id alone."""

    id: BookingId
    room_id: RoomId
    member_id: MemberId
    slot: TimeSlot
    price: Money
    status: BookingStatus
    held_at: datetime
    payment_id: str | None = None
    _events: list[BookingEvent] = field(
        default_factory=list, init=False, repr=False
    )

    @classmethod
    def hold(
        cls,
        *,
        booking_id: BookingId,
        room: Room,
        member_id: MemberId,
        slot: TimeSlot,
        now: datetime,
    ) -> Booking:
        if slot.start <= now:
            raise InvalidTimeSlot("a slot must start in the future")
        room.check_open(slot)
        booking = cls(
            id=booking_id,
            room_id=room.id,
            member_id=member_id,
            slot=slot,
            price=room.price_for(slot),
            status=BookingStatus.HELD,
            held_at=now,
        )
        booking._record(
            BookingHeld(
                booking_id=booking.id,
                room_id=booking.room_id,
                member_id=member_id,
                slot=slot,
                price=booking.price,
                expires_at=booking.expires_at,
                occurred_at=now,
            )
        )
        return booking

    @property
    def expires_at(self) -> datetime:
        return self.held_at + HOLD_DURATION

    def confirm(self, payment_id: str, now: datetime) -> None:
        if self._already_confirmed_by(payment_id):
            return
        if (
            self.status is BookingStatus.HELD
            and now >= self.expires_at
        ):
            raise IllegalTransition(
                f"hold {self.id} expired at {self._expiry()}"
            )
        self._become(BookingStatus.CONFIRMED)
        self.payment_id = payment_id
        self._record(
            BookingConfirmed(
                booking_id=self.id,
                member_id=self.member_id,
                payment_id=payment_id,
                occurred_at=now,
            )
        )

    def cancel(self, now: datetime) -> CancellationTerms:
        if now >= self.slot.start:
            raise IllegalTransition(
                f"booking {self.id} has already started"
            )
        terms = cancellation_terms(
            self._paid(), self.slot.start, now
        )
        self._become(BookingStatus.CANCELLED)
        self._record(
            BookingCancelled(
                booking_id=self.id,
                member_id=self.member_id,
                fee=terms.fee,
                refund=terms.refund,
                occurred_at=now,
            )
        )
        return terms

    def expire(self, now: datetime) -> None:
        if (
            self.status is BookingStatus.HELD
            and now < self.expires_at
        ):
            raise IllegalTransition(
                f"hold {self.id} runs until {self._expiry()}"
            )
        self._become(BookingStatus.EXPIRED)
        self._record(
            HoldExpired(
                booking_id=self.id,
                member_id=self.member_id,
                occurred_at=now,
            )
        )

    def pull_events(self) -> list[BookingEvent]:
        """Hand over the recorded events and forget them."""
        events, self._events = self._events, []
        return events

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Booking) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def _already_confirmed_by(self, payment_id: str) -> bool:
        return (
            self.status is BookingStatus.CONFIRMED
            and self.payment_id == payment_id
        )

    def _expiry(self) -> str:
        return self.expires_at.isoformat(timespec="minutes")

    def _paid(self) -> Money:
        if self.status is BookingStatus.CONFIRMED:
            return self.price
        return Money.zero(self.price.currency)

    def _become(self, target: BookingStatus) -> None:
        if target not in _NEXT[self.status]:
            raise IllegalTransition(
                f"booking {self.id} is {self.status}; "
                f"it cannot become {target}"
            )
        self.status = target

    def _record(self, event: BookingEvent) -> None:
        self._events.append(event)
