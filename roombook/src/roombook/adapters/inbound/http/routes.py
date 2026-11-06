"""Routes: parse, call one use case, translate the answer."""

from datetime import date

from fastapi import APIRouter, status

from roombook.adapters.inbound.http.dependencies import (
    CancelBookingDep,
    HoldRoomDep,
    ListAvailabilityDep,
    MemberIdDep,
)
from roombook.adapters.inbound.http.schemas import (
    AvailabilityResponse,
    CancellationResponse,
    HoldRequest,
    HoldResponse,
)
from roombook.application.cancel_booking import CancelBookingCommand
from roombook.application.list_availability import AvailabilityQuery
from roombook.domain.ids import BookingId, RoomId

router = APIRouter()


@router.post("/holds", status_code=status.HTTP_201_CREATED)
async def hold_room(
    body: HoldRequest, member: MemberIdDep, hold: HoldRoomDep
) -> HoldResponse:
    receipt = await hold(body.to_command(member))
    return HoldResponse.of(receipt)


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, member: MemberIdDep, cancel: CancelBookingDep
) -> CancellationResponse:
    command = CancelBookingCommand(
        booking_id=BookingId(booking_id), member_id=member
    )
    return CancellationResponse.of(await cancel(command))


@router.get("/rooms/{room_id}/availability")
async def availability(
    room_id: str, day: date, list_free: ListAvailabilityDep
) -> AvailabilityResponse:
    query = AvailabilityQuery(room_id=RoomId(room_id), day=day)
    return AvailabilityResponse.of(await list_free(query))
