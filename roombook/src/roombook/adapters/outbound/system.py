"""The real clock and the real id generator."""

import uuid
from datetime import UTC, datetime

from roombook.domain.ids import BookingId


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class Uuid7Ids:
    """Time-ordered ids, so new rows land at the index's end."""

    def new_booking_id(self) -> BookingId:
        return BookingId(str(uuid.uuid7()))
