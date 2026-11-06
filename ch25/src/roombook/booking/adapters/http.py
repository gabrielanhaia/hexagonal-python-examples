from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from roombook.booking.application import (
    CancelBooking,
    HoldRoom,
    HoldRoomCommand,
)
from roombook.booking.domain import (
    BookingError,
    IllegalTransition,
    NotFound,
    SlotUnavailable,
)

router = APIRouter(tags=["booking"])


class HoldIn(BaseModel):
    member_id: str
    start: datetime
    end: datetime


class HoldOut(BaseModel):
    booking_id: str
    price: int
    currency: str


class CancelOut(BaseModel):
    booking_id: str
    fee: int
    currency: str


def hold_room(request: Request) -> HoldRoom:
    return cast(HoldRoom, request.app.state.hold_room)


def cancel_booking(request: Request) -> CancelBooking:
    return cast(CancelBooking, request.app.state.cancel_booking)


def http_error(error: BookingError) -> HTTPException:
    match error:
        case NotFound():
            return HTTPException(404, str(error))
        case SlotUnavailable() | IllegalTransition():
            return HTTPException(409, str(error))
        case _:
            return HTTPException(422, str(error))


@router.post("/rooms/{room_id}/holds", status_code=201)
async def post_hold(
    room_id: str,
    body: HoldIn,
    hold: Annotated[HoldRoom, Depends(hold_room)],
) -> HoldOut:
    command = HoldRoomCommand(
        room_id=room_id,
        member_id=body.member_id,
        start=body.start,
        end=body.end,
    )
    try:
        booking = await hold(command)
    except BookingError as error:
        raise http_error(error) from error
    return HoldOut(
        booking_id=booking.id,
        price=booking.price.amount,
        currency=booking.price.currency,
    )


@router.post("/bookings/{booking_id}/cancel")
async def post_cancel(
    booking_id: str,
    cancel: Annotated[CancelBooking, Depends(cancel_booking)],
) -> CancelOut:
    try:
        fee = await cancel(booking_id)
    except BookingError as error:
        raise http_error(error) from error
    return CancelOut(
        booking_id=booking_id, fee=fee.amount, currency=fee.currency
    )
