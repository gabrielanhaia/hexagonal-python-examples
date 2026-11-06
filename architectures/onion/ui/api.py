from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from application_services.booking_service import (
    BookingApplicationService,
)
from domain_model.errors import (
    BookingNotFound,
    DomainError,
    IllegalTransition,
    RoomNotFound,
    SlotUnavailable,
)
from domain_model.values import Money

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


def booking_service(request: Request) -> BookingApplicationService:
    return cast(
        BookingApplicationService, request.app.state.bookings
    )


BookingServiceDep = Annotated[
    BookingApplicationService, Depends(booking_service)
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
    room_id: str, body: HoldRequest, service: BookingServiceDep
) -> HoldResponse:
    try:
        booking = await service.hold_room(
            room_id=room_id,
            member_id=body.member_id,
            start=body.start,
            end=body.end,
        )
    except DomainError as error:
        raise http_error(error) from error
    return HoldResponse(
        booking_id=booking.id,
        status=booking.status,
        price=MoneyOut.of(booking.price),
    )


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, service: BookingServiceDep
) -> CancelResponse:
    try:
        cancellation = await service.cancel_booking(booking_id)
    except DomainError as error:
        raise http_error(error) from error
    return CancelResponse(
        booking_id=cancellation.booking.id,
        status=cancellation.booking.status,
        fee=MoneyOut.of(cancellation.fee),
    )
