from datetime import UTC, datetime

from roombook.domain.booking import Booking


def at(hour: int) -> datetime:
    return datetime(2026, 11, 10, hour, tzinfo=UTC)


def test_bookings_of_one_room_overlap() -> None:
    first = Booking(
        id="b-1", room_id="atlas", starts_at=at(10), ends_at=at(12)
    )
    second = Booking(
        id="b-2", room_id="atlas", starts_at=at(11), ends_at=at(13)
    )

    assert first.overlaps(second)
