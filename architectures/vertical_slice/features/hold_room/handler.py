from datetime import UTC, timedelta
from uuid import uuid4

from features.hold_room.request import HoldRoomRequest
from features.hold_room.response import HoldRoomResponse, Price
from features.hold_room.store import HoldRoomStore
from kernel.database import BookingRow
from kernel.errors import Conflict, NotFound, Rejected


async def hold_room(
    room_id: str, request: HoldRoomRequest, store: HoldRoomStore
) -> HoldRoomResponse:
    room = await store.room(room_id)
    if room is None:
        raise NotFound(f"no room {room_id}")
    start = request.start.astimezone(UTC)
    end = request.end.astimezone(UTC)
    if not (
        start.date() == end.date()
        and room.opens <= start.time()
        and end.time() <= room.closes
    ):
        raise Rejected(f"{room.name} is closed then")
    if await store.is_taken(room_id, start, end):
        raise Conflict(f"{room.name} is taken then")
    minutes = (end - start) // timedelta(minutes=1)
    booking = BookingRow(
        id=uuid4().hex,
        room_id=room_id,
        member_id=request.member_id,
        starts_at=start,
        ends_at=end,
        price=room.hourly_rate * minutes // 60,
        currency=room.currency,
        status="HELD",
    )
    await store.insert(booking)
    return HoldRoomResponse(
        booking_id=booking.id,
        status=booking.status,
        price=Price(
            amount=booking.price, currency=booking.currency
        ),
    )
