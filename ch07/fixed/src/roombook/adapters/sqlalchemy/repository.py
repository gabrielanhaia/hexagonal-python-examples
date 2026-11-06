from sqlalchemy.ext.asyncio import AsyncSession

from roombook.adapters.sqlalchemy.records import (
    BookingRecord,
    to_domain,
    to_record,
)
from roombook.domain.booking import Booking


class SqlAlchemyBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, booking_id: str) -> Booking | None:
        record = await self._session.get(BookingRecord, booking_id)
        return None if record is None else to_domain(record)

    async def save(self, booking: Booking) -> None:
        await self._session.merge(to_record(booking))
