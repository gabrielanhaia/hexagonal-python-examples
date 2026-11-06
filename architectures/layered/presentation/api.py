from collections.abc import AsyncIterator, Callable
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from data_access.bookings import BookingDAO
from presentation.schemas import (
    CancelResponse,
    HoldRequest,
    HoldResponse,
    MoneyOut,
)
from services.booking_service import BookingService
from services.errors import (
    BookingError,
    BookingNotFound,
    IllegalTransition,
    RoomNotFound,
    SlotUnavailable,
)

router = APIRouter()


async def booking_service(
    request: Request,
) -> AsyncIterator[BookingService]:
    state = request.app.state
    sessions = cast(
        async_sessionmaker[AsyncSession], state.sessions
    )
    clock = cast(Callable[[], datetime], state.clock)
    async with sessions() as session:
        yield BookingService(BookingDAO(session), clock=clock)


BookingServiceDep = Annotated[
    BookingService, Depends(booking_service)
]


def http_error(error: BookingError) -> HTTPException:
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
    except BookingError as error:
        raise http_error(error) from error
    return HoldResponse(
        booking_id=booking.id,
        status=booking.status,
        price=MoneyOut(
            amount=booking.price, currency=booking.currency
        ),
    )


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, service: BookingServiceDep
) -> CancelResponse:
    try:
        cancellation = await service.cancel_booking(booking_id)
    except BookingError as error:
        raise http_error(error) from error
    booking = cancellation.booking
    return CancelResponse(
        booking_id=booking.id,
        status=booking.status,
        fee=MoneyOut(
            amount=cancellation.fee, currency=booking.currency
        ),
    )
