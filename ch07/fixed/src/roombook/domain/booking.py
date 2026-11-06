from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True, kw_only=True)
class Booking:
    id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus = BookingStatus.HELD

    def overlaps(self, other: Booking) -> bool:
        return (
            self.room_id == other.room_id
            and self.starts_at < other.ends_at
            and other.starts_at < self.ends_at
        )
