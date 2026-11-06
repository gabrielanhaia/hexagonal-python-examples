"""The Room repository: load the whole aggregate, save it whole."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from roombook.adapters.sqlalchemy.mappers import (
    reconcile,
    to_domain,
    to_record,
)
from roombook.adapters.sqlalchemy.records import RoomRecord
from roombook.domain.room import Room, RoomId


class SqlAlchemyRoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, room_id: RoomId) -> Room | None:
        record = await self._load(room_id)
        return None if record is None else to_domain(record)

    async def save(self, room: Room) -> None:
        record = await self._load(room.id)
        if record is None:
            self._session.add(to_record(room))
            return
        record.name = room.name
        reconcile(record.blackouts, room.blackouts)

    async def _load(self, room_id: RoomId) -> RoomRecord | None:
        statement = (
            select(RoomRecord)
            .where(RoomRecord.id == room_id)
            .options(selectinload(RoomRecord.blackouts))
        )
        return await self._session.scalar(statement)
