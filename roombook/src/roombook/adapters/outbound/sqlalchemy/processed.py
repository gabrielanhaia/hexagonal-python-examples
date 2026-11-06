"""Message ids a consumer has already handled."""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.sqlalchemy.records import (
    ProcessedMessageRecord,
)


class SqlAlchemyProcessedMessages:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        self._sessions = sessions

    async def seen(self, message_id: str) -> bool:
        async with self._sessions() as session:
            record = await session.get(
                ProcessedMessageRecord, message_id
            )
            return record is not None

    async def remember(self, message_id: str) -> None:
        statement = (
            insert(ProcessedMessageRecord)
            .values(message_id=message_id, processed_at=func.now())
            .on_conflict_do_nothing()
        )
        async with self._sessions.begin() as session:
            await session.execute(statement)
