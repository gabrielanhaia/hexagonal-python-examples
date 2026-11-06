from datetime import datetime

from kernel.database import BookingRow, Database, RoomRow


class HoldRoomStore:
    def __init__(self, database: Database) -> None:
        self._db = database

    async def room(self, room_id: str) -> RoomRow | None:
        return self._db.rooms.get(room_id)

    async def is_taken(
        self, room_id: str, start: datetime, end: datetime
    ) -> bool:
        return any(
            row.room_id == room_id
            and row.status in ("HELD", "CONFIRMED")
            and row.starts_at < end
            and start < row.ends_at
            for row in self._db.bookings.values()
        )

    async def insert(self, booking: BookingRow) -> None:
        self._db.bookings[booking.id] = booking
