from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from data_access.bookings import BookingDAO
from data_access.models import ACTIVE, Booking, BookingStatus, Room
from services.errors import (
    BookingNotFound,
    IllegalTransition,
    InvalidTimeSlot,
    OutsideOpeningHours,
    RoomNotFound,
    SlotUnavailable,
)

FREE_CANCELLATION_NOTICE = timedelta(hours=24)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class Cancellation:
    booking: Booking
    fee: int  # minor units, same currency as the booking


class BookingService:
    def __init__(
        self,
        dao: BookingDAO,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._dao = dao
        self._clock = clock

    async def hold_room(
        self,
        *,
        room_id: str,
        member_id: str,
        start: datetime,
        end: datetime,
    ) -> Booking:
        check_slot(start, end)
        room = await self._dao.get_room(room_id)
        if room is None:
            raise RoomNotFound(room_id)
        if not is_open(room, start, end):
            raise OutsideOpeningHours(f"{room.name} is closed then")
        if await self._dao.has_overlap(room_id, start, end):
            raise SlotUnavailable(f"{room.name} is taken then")
        minutes = (end - start) // timedelta(minutes=1)
        booking = Booking(
            id=uuid4().hex,
            room_id=room.id,
            member_id=member_id,
            starts_at=start,
            ends_at=end,
            price=room.hourly_rate * minutes // 60,
            currency=room.currency,
            status=BookingStatus.HELD,
        )
        self._dao.add(booking)
        await self._dao.commit()
        return booking

    async def cancel_booking(self, booking_id: str) -> Cancellation:
        booking = await self._dao.get_booking(booking_id)
        if booking is None:
            raise BookingNotFound(booking_id)
        if booking.status not in ACTIVE:
            raise IllegalTransition(f"booking is {booking.status}")
        booking.status = BookingStatus.CANCELLED
        await self._dao.commit()
        notice = booking.starts_at - self._clock()
        late = notice < FREE_CANCELLATION_NOTICE
        fee = booking.price // 2 if late else 0
        return Cancellation(booking=booking, fee=fee)


def check_slot(start: datetime, end: datetime) -> None:
    if start.tzinfo is None or end.tzinfo is None:
        raise InvalidTimeSlot("start and end need a timezone")
    if start >= end:
        raise InvalidTimeSlot("start must be before end")
    for moment in (start, end):
        if (
            moment.minute % 15
            or moment.second
            or moment.microsecond
        ):
            raise InvalidTimeSlot("slots move in 15-minute steps")


def is_open(room: Room, start: datetime, end: datetime) -> bool:
    start, end = start.astimezone(UTC), end.astimezone(UTC)
    return (
        start.date() == end.date()
        and room.opens <= start.time()
        and end.time() <= room.closes
    )
