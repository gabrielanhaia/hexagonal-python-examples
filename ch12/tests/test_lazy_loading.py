import pytest
from conftest import Sessions
from sqlalchemy.exc import MissingGreenlet, StatementError

from roombook.adapters.sqlalchemy.mappers import to_domain
from roombook.adapters.sqlalchemy.records import RoomRecord
from roombook.adapters.sqlalchemy.repository import (
    SqlAlchemyRoomRepository,
)
from roombook.domain.room import Room, RoomId


async def test_lazy_loading_fails_under_asyncio(
    sessions: Sessions, atlas: Room
) -> None:
    async with sessions() as session:
        record = await session.get(RoomRecord, "atlas")
        assert record is not None

        with pytest.raises(StatementError) as caught:
            to_domain(record)  # touches record.blackouts

    assert isinstance(caught.value.orig, MissingGreenlet)
    assert "greenlet_spawn has not been called" in str(caught.value)


async def test_the_repository_loads_children_eagerly(
    sessions: Sessions, atlas: Room
) -> None:
    async with sessions() as session:
        rooms = SqlAlchemyRoomRepository(session)
        room = await rooms.get(RoomId("atlas"))

    assert room is not None
    assert [b.id for b in room.blackouts] == ["paint", "carpet"]
