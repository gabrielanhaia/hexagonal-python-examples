"""The two adapters behind each port, behind one test interface."""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.memory.fakes import (
    InMemoryProcessedMessages,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
    InMemoryUnitOfWork,
)
from roombook.adapters.outbound.sqlalchemy.mappers import (
    room_to_record,
)
from roombook.adapters.outbound.sqlalchemy.processed import (
    SqlAlchemyProcessedMessages,
)
from roombook.adapters.outbound.sqlalchemy.records import (
    OutboxRecord,
)
from roombook.adapters.outbound.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from roombook.application.ports import UnitOfWork
from roombook.domain.room import Room


class ProcessedMessages(Protocol):
    async def seen(self, message_id: str) -> bool: ...

    async def remember(self, message_id: str) -> None: ...


class Backend(Protocol):
    def unit_of_work(self) -> UnitOfWork: ...

    def processed_messages(self) -> ProcessedMessages: ...

    async def add_room(self, room: Room) -> None: ...

    async def outbox_types(self) -> list[str]: ...


class MemoryBackend:
    def __init__(self) -> None:
        self._store = InMemoryStore()

    def unit_of_work(self) -> UnitOfWork:
        return InMemoryUnitOfWork(self._store)

    def processed_messages(self) -> ProcessedMessages:
        return InMemoryProcessedMessages()

    async def add_room(self, room: Room) -> None:
        self._store.rooms[room.id] = room

    async def outbox_types(self) -> list[str]:
        return [
            type(event).__name__ for event in self._store.outbox
        ]


class PostgresBackend:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        self._sessions = sessions

    def unit_of_work(self) -> UnitOfWork:
        return SqlAlchemyUnitOfWork(self._sessions)

    def processed_messages(self) -> ProcessedMessages:
        return SqlAlchemyProcessedMessages(self._sessions)

    async def add_room(self, room: Room) -> None:
        async with self._sessions.begin() as session:
            session.add(room_to_record(room))

    async def outbox_types(self) -> list[str]:
        query = select(OutboxRecord.type).order_by(OutboxRecord.id)
        async with self._sessions() as session:
            return list(await session.scalars(query))
