from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Literal

type BookingStatus = Literal["HELD", "CONFIRMED", "CANCELLED"]


@dataclass(slots=True, kw_only=True)
class RoomRow:
    id: str
    name: str
    hourly_rate: int  # minor units
    currency: str
    opens: time  # UTC
    closes: time


@dataclass(slots=True, kw_only=True)
class BookingRow:
    id: str
    room_id: str
    member_id: str
    starts_at: datetime
    ends_at: datetime
    price: int  # minor units
    currency: str
    status: BookingStatus


@dataclass(slots=True)
class Database:
    """The one thing every slice shares: the stored data."""

    rooms: dict[str, RoomRow] = field(default_factory=dict)
    bookings: dict[str, BookingRow] = field(default_factory=dict)
