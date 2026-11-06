"""Driven ports: what the use cases need from the world."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Self

from roombook.domain.booking import Booking
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId, RoomId
from roombook.domain.money import Money
from roombook.domain.room import Room
from roombook.domain.time_slot import TimeSlot


class BookingRepository(Protocol):
    async def add(self, booking: Booking) -> None:
        """Store a new booking. Raises SlotUnavailable."""
        ...

    async def get(self, booking_id: BookingId) -> Booking | None:
        """Load a booking for change; it stays locked."""
        ...

    async def save(self, booking: Booking) -> None: ...

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        """Held or confirmed bookings that overlap the slot."""
        ...

    async def stale_holds(self, now: datetime) -> list[Booking]:
        """Holds whose fifteen minutes ran out by now."""
        ...


class RoomRepository(Protocol):
    async def get(self, room_id: RoomId) -> Room | None: ...


class Outbox(Protocol):
    async def put(self, events: Sequence[BookingEvent]) -> None:
        """Queue events to publish once the work commits."""
        ...


class UnitOfWork(Protocol):
    """One transaction. Nothing persists without commit()."""

    @property
    def bookings(self) -> BookingRepository: ...

    @property
    def rooms(self) -> RoomRepository: ...

    @property
    def outbox(self) -> Outbox: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, *exc_info: object) -> None: ...

    async def commit(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_booking_id(self) -> BookingId: ...


@dataclass(frozen=True, slots=True)
class Checkout:
    id: str
    url: str


class PaymentUnavailable(Exception):
    """The payment provider could not take the request."""


class PaymentGateway(Protocol):
    async def start_checkout(
        self, booking_id: BookingId, amount: Money
    ) -> Checkout:
        """Open a checkout. Raises PaymentUnavailable."""
        ...


class Notifier(Protocol):
    async def notify(self, events: Sequence[BookingEvent]) -> None:
        """Tell members what happened to their bookings."""
        ...
