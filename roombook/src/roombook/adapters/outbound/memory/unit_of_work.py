"""A unit of work over dictionaries: commit or nothing."""

from dataclasses import dataclass, field
from typing import Self

from roombook.adapters.outbound.memory.repositories import (
    InMemoryBookingRepository,
    InMemoryOutbox,
    InMemoryRoomRepository,
)
from roombook.domain.booking import Booking
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId, RoomId
from roombook.domain.room import Room


@dataclass
class InMemoryStore:
    """What the fakes share: a stand-in for one database."""

    rooms: dict[RoomId, Room] = field(default_factory=dict)
    bookings: dict[BookingId, Booking] = field(default_factory=dict)
    outbox: list[BookingEvent] = field(default_factory=list)

    def unit_of_work(self) -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(self)


class InMemoryUnitOfWork:
    """Works on copies; commit() swaps them into the store."""

    bookings: InMemoryBookingRepository
    rooms: InMemoryRoomRepository
    outbox: InMemoryOutbox

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def __aenter__(self) -> Self:
        self.bookings = InMemoryBookingRepository(
            dict(self._store.bookings)
        )
        self.rooms = InMemoryRoomRepository(self._store.rooms)
        self.outbox = InMemoryOutbox()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Uncommitted copies are dropped with this object."""

    async def commit(self) -> None:
        self._store.bookings = dict(self.bookings.rows)
        self._store.outbox.extend(self.outbox.pending)
        self.outbox.pending.clear()
