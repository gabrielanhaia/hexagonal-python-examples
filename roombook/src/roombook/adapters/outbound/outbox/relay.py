"""Relay committed outbox rows to Kafka, at least once."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta

import structlog
from faststream.kafka import KafkaBroker
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.sqlalchemy.records import (
    OutboxRecord,
)

type Publish = Callable[[OutboxRecord], Awaitable[None]]

log = structlog.get_logger()


def kafka_publisher(broker: KafkaBroker) -> Publish:
    async def publish(record: OutboxRecord) -> None:
        await broker.publish(
            record.payload,
            record.topic,
            key=record.key.encode(),
            headers={
                "message-id": str(record.id),
                "event-type": record.type,
            },
        )

    return publish


class OutboxRelay:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        publish: Publish,
    ) -> None:
        self._sessions = sessions
        self._publish = publish

    async def relay_batch(self, limit: int = 100) -> int:
        """Publish up to `limit` rows; return how many."""
        pending = (
            select(OutboxRecord)
            .where(OutboxRecord.published_at.is_(None))
            .order_by(OutboxRecord.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        async with self._sessions.begin() as session:
            records = (await session.scalars(pending)).all()
            for record in records:
                await self._publish(record)
            await session.execute(
                update(OutboxRecord)
                .where(OutboxRecord.id.in_([r.id for r in records]))
                .values(published_at=func.now())
            )
        if records:
            await log.ainfo("outbox relayed", count=len(records))
        return len(records)

    async def run(self, *, idle: timedelta) -> None:
        """Relay forever, resting for `idle` when caught up."""
        while True:
            if await self.relay_batch() == 0:
                await asyncio.sleep(idle.total_seconds())
