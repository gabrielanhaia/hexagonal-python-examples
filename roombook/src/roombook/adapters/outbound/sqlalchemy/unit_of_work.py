"""The unit of work: one AsyncSession, one transaction."""

from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.sqlalchemy.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyOutbox,
    SqlAlchemyRoomRepository,
)


class SqlAlchemyUnitOfWork:
    bookings: SqlAlchemyBookingRepository
    rooms: SqlAlchemyRoomRepository
    outbox: SqlAlchemyOutbox

    def __init__(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        self._sessions = sessions

    async def __aenter__(self) -> Self:
        self._session = self._sessions()
        self.bookings = SqlAlchemyBookingRepository(self._session)
        self.rooms = SqlAlchemyRoomRepository(self._session)
        self.outbox = SqlAlchemyOutbox(self._session)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._session.close()  # rolls back if not committed

    async def commit(self) -> None:
        await self._session.commit()
