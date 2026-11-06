from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_access.models import ACTIVE, Booking, Room


class BookingDAO:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_room(self, room_id: str) -> Room | None:
        return await self._session.get(Room, room_id)

    async def get_booking(self, booking_id: str) -> Booking | None:
        return await self._session.get(Booking, booking_id)

    async def has_overlap(
        self, room_id: str, starts_at: datetime, ends_at: datetime
    ) -> bool:
        query = (
            select(Booking.id)
            .where(
                Booking.room_id == room_id,
                Booking.status.in_(ACTIVE),
                Booking.starts_at < ends_at,
                Booking.ends_at > starts_at,
            )
            .limit(1)
        )
        return await self._session.scalar(query) is not None

    def add(self, booking: Booking) -> None:
        self._session.add(booking)

    async def commit(self) -> None:
        await self._session.commit()
