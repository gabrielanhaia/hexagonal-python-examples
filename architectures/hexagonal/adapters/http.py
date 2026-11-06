from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from application.cancel_booking import CancelBooking
from application.hold_room import HoldRoom, HoldRoomCommand
from domain.errors import (
    BookingNotFound,
    DomainError,
    IllegalTransition,
    RoomNotFound,
    SlotUnavailable,
)
from domain.values import Money

router = APIRouter()


class HoldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: str
    start: datetime
    end: datetime


class MoneyOut(BaseModel):
    amount: int
    currency: str

    @classmethod
    def of(cls, money: Money) -> MoneyOut:
        return cls(amount=money.amount, currency=money.currency)


class HoldResponse(BaseModel):
    booking_id: str
    status: str
    price: MoneyOut


class CancelResponse(BaseModel):
    booking_id: str
    status: str
    fee: MoneyOut


def hold_room_use_case(request: Request) -> HoldRoom:
    return cast(HoldRoom, request.app.state.hold_room)


def cancel_booking_use_case(request: Request) -> CancelBooking:
    return cast(CancelBooking, request.app.state.cancel_booking)


HoldRoomDep = Annotated[HoldRoom, Depends(hold_room_use_case)]
CancelBookingDep = Annotated[
    CancelBooking, Depends(cancel_booking_use_case)
]


def http_error(error: DomainError) -> HTTPException:
    match error:
        case RoomNotFound() | BookingNotFound():
            status = 404
        case SlotUnavailable() | IllegalTransition():
            status = 409
        case _:
            status = 422
    return HTTPException(status_code=status, detail=str(error))


@router.post("/rooms/{room_id}/holds", status_code=201)
async def hold_room(
    room_id: str, body: HoldRequest, hold: HoldRoomDep
) -> HoldResponse:
    command = HoldRoomCommand(
        room_id=room_id,
        member_id=body.member_id,
        start=body.start,
        end=body.end,
    )
    try:
        booking = await hold(command)
    except DomainError as error:
        raise http_error(error) from error
    return HoldResponse(
        booking_id=booking.id,
        status=booking.status,
        price=MoneyOut.of(booking.price),
    )


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, cancel: CancelBookingDep
) -> CancelResponse:
    try:
        cancellation = await cancel(booking_id)
    except DomainError as error:
        raise http_error(error) from error
    return CancelResponse(
        booking_id=cancellation.booking.id,
        status=cancellation.booking.status,
        fee=MoneyOut.of(cancellation.fee),
    )
