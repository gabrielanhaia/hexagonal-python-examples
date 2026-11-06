from typing import Protocol

from roombook.domain.booking import Booking


class BookingRepository(Protocol):
    async def get(self, booking_id: str) -> Booking | None: ...

    async def save(self, booking: Booking) -> None: ...
