from dataclasses import replace

from kernel.database import BookingRow, Database


class CancelBookingStore:
    def __init__(self, database: Database) -> None:
        self._db = database

    async def booking(self, booking_id: str) -> BookingRow | None:
        row = self._db.bookings.get(booking_id)
        return None if row is None else replace(row)

    async def update(self, booking: BookingRow) -> None:
        self._db.bookings[booking.id] = booking
