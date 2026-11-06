from conftest import Sessions, blackout, slot
from sqlalchemy import select

from roombook.adapters.sqlalchemy.records import BlackoutRecord
from roombook.adapters.sqlalchemy.repository import (
    SqlAlchemyRoomRepository,
)
from roombook.domain.room import BlackoutId, Room, RoomId


async def rows(sessions: Sessions) -> list[tuple[str, int]]:
    statement = select(BlackoutRecord).order_by(BlackoutRecord.id)
    async with sessions() as session:
        records = await session.scalars(statement)
        return [(r.id, r.starts_at.day) for r in records]


async def load(sessions: Sessions, room_id: str) -> Room:
    async with sessions() as session:
        room = await SqlAlchemyRoomRepository(session).get(
            RoomId(room_id)
        )
    assert room is not None
    return room


async def save(sessions: Sessions, room: Room) -> None:
    async with sessions.begin() as session:
        await SqlAlchemyRoomRepository(session).save(room)


async def test_a_new_room_saves_its_blackouts(
    sessions: Sessions, atlas: Room
) -> None:
    assert await rows(sessions) == [("carpet", 2), ("paint", 1)]


async def test_removing_a_blackout_deletes_its_row(
    sessions: Sessions, atlas: Room
) -> None:
    room = await load(sessions, "atlas")
    room.remove_blackout(BlackoutId("paint"))
    await save(sessions, room)

    assert await rows(sessions) == [("carpet", 2)]


async def test_save_adds_and_updates_by_identity(
    sessions: Sessions, atlas: Room
) -> None:
    room = await load(sessions, "atlas")
    room.add_blackout(blackout("lights", 3))
    room.reschedule_blackout(BlackoutId("carpet"), slot(4, 8, 9))
    await save(sessions, room)

    assert await rows(sessions) == [
        ("carpet", 4),
        ("lights", 3),
        ("paint", 1),
    ]
