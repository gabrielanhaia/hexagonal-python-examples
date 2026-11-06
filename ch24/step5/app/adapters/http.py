"""The driving HTTP adapter; FastAPI's Depends does the wiring."""

from datetime import UTC
from typing import Annotated

import httpx2
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.clock import SystemClock
from app.adapters.schemas import BookingOut, CancellationOut, HoldIn
from app.adapters.sqlalchemy.database import get_session
from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyRoomRepository,
)
from app.adapters.tillpoint import TillpointPayments, get_tillpoint
from app.application.cancel_booking import CancelBooking
from app.application.confirm_booking import ConfirmBooking
from app.application.hold_room import HoldRoom, HoldRoomCommand
from app.domain.errors import (
    BookingNotFound,
    DomainError,
    HoldExpired,
    IllegalTransition,
    InvalidTimeSlot,
    OutsideOpeningHours,
    PaymentDeclined,
    RoomNotFound,
    SlotUnavailable,
)

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
TillpointDep = Annotated[httpx2.AsyncClient, Depends(get_tillpoint)]


def hold_room_use_case(session: SessionDep) -> HoldRoom:
    return HoldRoom(
        rooms=SqlAlchemyRoomRepository(session),
        bookings=SqlAlchemyBookingRepository(session),
        clock=SystemClock(),
    )


def confirm_booking_use_case(
    session: SessionDep, tillpoint: TillpointDep
) -> ConfirmBooking:
    return ConfirmBooking(
        bookings=SqlAlchemyBookingRepository(session),
        payments=TillpointPayments(tillpoint),
        clock=SystemClock(),
    )


def cancel_booking_use_case(session: SessionDep) -> CancelBooking:
    return CancelBooking(
        bookings=SqlAlchemyBookingRepository(session),
        clock=SystemClock(),
    )


HoldRoomDep = Annotated[HoldRoom, Depends(hold_room_use_case)]
ConfirmBookingDep = Annotated[
    ConfirmBooking, Depends(confirm_booking_use_case)
]
CancelBookingDep = Annotated[
    CancelBooking, Depends(cancel_booking_use_case)
]


def http_error(error: DomainError) -> HTTPException:
    match error:
        case RoomNotFound() | BookingNotFound():
            status = 404
        case InvalidTimeSlot() | OutsideOpeningHours():
            status = 422
        case (
            SlotUnavailable() | IllegalTransition() | HoldExpired()
        ):
            status = 409
        case PaymentDeclined():
            status = 402
        case _:
            status = 400
    return HTTPException(status, str(error))


@router.post("/rooms/{room_id}/holds", status_code=201)
async def hold_room(
    room_id: str, body: HoldIn, hold: HoldRoomDep
) -> BookingOut:
    command = HoldRoomCommand(
        room_id=room_id,
        member_id=body.member_id,
        start=body.start.astimezone(UTC),
        end=body.end.astimezone(UTC),
    )
    try:
        booking = await hold(command)
    except DomainError as error:
        raise http_error(error) from error
    return BookingOut.of(booking)


@router.post("/bookings/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str, confirm: ConfirmBookingDep
) -> BookingOut:
    try:
        booking = await confirm(booking_id)
    except DomainError as error:
        raise http_error(error) from error
    return BookingOut.of(booking)


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, cancel: CancelBookingDep
) -> CancellationOut:
    try:
        cancellation = await cancel(booking_id)
    except DomainError as error:
        raise http_error(error) from error
    return CancellationOut(
        booking_id=cancellation.booking.id,
        status=cancellation.booking.status,
        fee_cents=cancellation.fee.amount,
        currency=cancellation.fee.currency,
    )
