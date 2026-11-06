from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time, timedelta
from typing import Annotated

import httpx2
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, engine, get_session
from app.models import HOLD_TTL, Base, Booking, Room
from app.schemas import BookingOut, CancellationOut, HoldIn
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        if await session.get(Room, "atlas") is None:
            session.add(  # demo data, so the service runs as is
                Room(
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


@app.post("/rooms/{room_id}/holds", status_code=201)
async def hold_room(
    room_id: str, body: HoldIn, session: SessionDep
) -> BookingOut:
    room = await session.get(Room, room_id)
    if room is None:
        raise HTTPException(404, "Room not found")
    start = body.start.astimezone(UTC)
    end = body.end.astimezone(UTC)
    if (
        start.date() != end.date()
        or start.time() < room.opens_at
        or end.time() > room.closes_at
    ):
        raise HTTPException(422, "Room is closed at that time")
    now = datetime.now(UTC)
    clash = await session.scalar(
        select(Booking.id)
        .where(
            Booking.room_id == room_id,
            Booking.starts_at < end,
            Booking.ends_at > start,
            or_(
                Booking.status == "CONFIRMED",
                and_(
                    Booking.status == "HELD",
                    Booking.created_at > now - HOLD_TTL,
                ),
            ),
        )
        .limit(1)
    )
    if clash is not None:
        raise HTTPException(409, "Room is already booked")
    minutes = (end - start) // timedelta(minutes=1)
    booking = Booking(
        room_id=room.id,
        member_id=body.member_id,
        starts_at=start,
        ends_at=end,
        price_cents=room.hourly_rate_cents * minutes // 60,
        currency=room.currency,
    )
    session.add(booking)
    await session.commit()
    return BookingOut.model_validate(booking)


@app.post("/bookings/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str, session: SessionDep, tillpoint: TillpointDep
) -> BookingOut:
    booking = await session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    if booking.status != "HELD":
        raise HTTPException(409, f"Booking is {booking.status}")
    if booking.is_expired:
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
    booking = await session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    if booking.status not in ("HELD", "CONFIRMED"):
        raise HTTPException(409, f"Booking is {booking.status}")
    fee = booking.cancellation_fee()
    booking.status = "CANCELLED"
    booking.cancellation_fee_cents = fee
    await session.commit()
    return CancellationOut(
        booking_id=booking.id,
        status=booking.status,
        fee_cents=fee,
        currency=booking.currency,
    )
