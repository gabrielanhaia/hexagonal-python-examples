from datetime import timedelta

from features.cancel_booking.request import CancelBookingRequest
from features.cancel_booking.response import (
    CancelBookingResponse,
    Fee,
)
from features.cancel_booking.store import CancelBookingStore
from kernel.dependencies import Clock
from kernel.errors import Conflict, NotFound

FREE_CANCELLATION_NOTICE = timedelta(hours=24)


async def cancel_booking(
    request: CancelBookingRequest,
    store: CancelBookingStore,
    clock: Clock,
) -> CancelBookingResponse:
    booking = await store.booking(request.booking_id)
    if booking is None:
        raise NotFound(f"no booking {request.booking_id}")
    if booking.status not in ("HELD", "CONFIRMED"):
        raise Conflict(f"booking is {booking.status}")
    booking.status = "CANCELLED"
    await store.update(booking)
    late = booking.starts_at - clock() < FREE_CANCELLATION_NOTICE
    return CancelBookingResponse(
        booking_id=booking.id,
        status=booking.status,
        fee=Fee(
            amount=booking.price // 2 if late else 0,
            currency=booking.currency,
        ),
    )
