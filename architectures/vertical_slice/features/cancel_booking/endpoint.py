from fastapi import APIRouter

from features.cancel_booking.handler import cancel_booking
from features.cancel_booking.request import CancelBookingRequest
from features.cancel_booking.response import CancelBookingResponse
from features.cancel_booking.store import CancelBookingStore
from kernel.dependencies import ClockDep, DatabaseDep

router = APIRouter()


@router.post("/bookings/{booking_id}/cancel")
async def post_cancel(
    booking_id: str, database: DatabaseDep, clock: ClockDep
) -> CancelBookingResponse:
    return await cancel_booking(
        CancelBookingRequest(booking_id=booking_id),
        CancelBookingStore(database),
        clock,
    )
