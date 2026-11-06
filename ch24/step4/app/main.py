from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time
from typing import Annotated

import httpx2
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.clock import SystemClock
from app.adapters.sqlalchemy_repository import (
    SqlAlchemyBookingRepository,
    SqlAlchemyRoomRepository,
)
from app.application.hold_room import HoldRoom, HoldRoomCommand
from app.db import SessionLocal, engine, get_session
from app.domain.booking import (
    Booking,
    cancellation_fee,
    hold_expired,
)
from app.domain.errors import (
    DomainError,
    OutsideOpeningHours,
    RoomNotFound,
    SlotUnavailable,
)
from app.domain.values import Money
from app.models import Base, BookingRow, RoomRow
from app.schemas import BookingOut, CancellationOut, HoldIn
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        if await session.get(RoomRow, "atlas") is None:
            session.add(  # demo data, so the service runs as is
                RoomRow(
                    id="atlas",
                    name="Atlas",
                    capacity=8,
                    hourly_rate_cents=2400,
                    currency="EUR",
                    opens_at=time(8),
                    closes_at=time(20),
                )
            )
            await session.commit()
    yield
    await engine.dispose()


app = FastAPI(title="roombook", lifespan=lifespan)


async def get_tillpoint() -> AsyncIterator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient(
        base_url=settings.tillpoint_url,
        headers={
            "Authorization": f"Bearer {settings.tillpoint_api_key}"
        },
        timeout=10,
    ) as client:
        yield client


SessionDep = Annotated[AsyncSession, Depends(get_session)]
TillpointDep = Annotated[httpx2.AsyncClient, Depends(get_tillpoint)]


def get_hold_room(session: SessionDep) -> HoldRoom:
    return HoldRoom(
        rooms=SqlAlchemyRoomRepository(session),
        bookings=SqlAlchemyBookingRepository(session),
        clock=SystemClock(),
    )


HoldRoomDep = Annotated[HoldRoom, Depends(get_hold_room)]


def http_error(error: DomainError) -> HTTPException:
    match error:
        case RoomNotFound():
            status = 404
        case OutsideOpeningHours():
            status = 422
        case SlotUnavailable():
            status = 409
        case _:
            status = 400
    return HTTPException(status, str(error))


def booking_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        room_id=booking.room_id,
        member_id=booking.member_id,
        starts_at=booking.slot.start,
        ends_at=booking.slot.end,
        status=booking.status,
        price_cents=booking.price.amount,
        currency=booking.price.currency,
    )


@app.post("/rooms/{room_id}/holds", status_code=201)
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
    return booking_out(booking)


@app.post("/bookings/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str, session: SessionDep, tillpoint: TillpointDep
) -> BookingOut:
    booking = await session.get(BookingRow, booking_id)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    if booking.status != "HELD":
        raise HTTPException(409, f"Booking is {booking.status}")
    if hold_expired(booking.created_at, datetime.now(UTC)):
        booking.status = "EXPIRED"
        await session.commit()
        raise HTTPException(409, "Hold expired")
    response = await tillpoint.post(
        "/v1/charges",
        json={
            "amount": booking.price_cents,
            "currency": booking.currency,
            "reference": booking.id,
        },
    )
    if response.status_code != 201:
        raise HTTPException(402, "Payment declined")
    booking.status = "CONFIRMED"
    booking.payment_id = response.json()["id"]
    await session.commit()
    return BookingOut.model_validate(booking)


@app.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, session: SessionDep
) -> CancellationOut:
    booking = await session.get(BookingRow, booking_id)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    if booking.status not in ("HELD", "CONFIRMED"):
        raise HTTPException(409, f"Booking is {booking.status}")
    price = Money(
        amount=booking.price_cents, currency=booking.currency
    )
    fee = cancellation_fee(
        price, booking.starts_at, datetime.now(UTC)
    )
    booking.status = "CANCELLED"
    booking.cancellation_fee_cents = fee.amount
    await session.commit()
    return CancellationOut(
        booking_id=booking.id,
        status=booking.status,
        fee_cents=fee.amount,
        currency=fee.currency,
    )
