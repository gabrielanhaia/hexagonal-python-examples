from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from roombook.adapters.sqlalchemy.records import Base
from roombook.adapters.sqlalchemy.repository import (
    SqlAlchemyRoomRepository,
)
from roombook.domain.room import (
    BlackoutId,
    BlackoutPeriod,
    Room,
    RoomId,
)
from roombook.domain.time_slot import TimeSlot

type Sessions = async_sessionmaker[AsyncSession]


def slot(day: int, start: int, end: int) -> TimeSlot:
    return TimeSlot(
        datetime(2026, 12, day, start, tzinfo=UTC),
        datetime(2026, 12, day, end, tzinfo=UTC),
    )


def blackout(name: str, day: int) -> BlackoutPeriod:
    return BlackoutPeriod(
        id=BlackoutId(name),
        slot=slot(day, 8, 12),
        reason="maintenance",
    )


@pytest.fixture
async def sessions(tmp_path: Path) -> AsyncIterator[Sessions]:
    url = f"sqlite+aiosqlite:///{tmp_path / 'ch12.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def atlas(sessions: Sessions) -> Room:
    room = Room(RoomId("atlas"), "Atlas")
    room.add_blackout(blackout("paint", 1))
    room.add_blackout(blackout("carpet", 2))
    async with sessions.begin() as session:
        await SqlAlchemyRoomRepository(session).save(room)
    return room
