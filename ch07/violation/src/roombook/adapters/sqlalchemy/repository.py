from sqlalchemy.ext.asyncio import AsyncSession

from roombook.domain.booking import Booking


class SqlAlchemyBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, booking_id: str) -> Booking | None:
        return await self._session.get(Booking, booking_id)

    async def save(self, booking: Booking) -> None:
        self._session.add(booking)
