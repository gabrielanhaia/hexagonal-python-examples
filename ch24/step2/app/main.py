from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time
from typing import Annotated

import httpx2
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, engine, get_session
from app.domain.booking import (
    cancellation_fee,
    hold_cutoff,
    hold_expired,
)
from app.domain.room import OpeningHours, Room
from app.domain.values import Money, TimeSlot
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


async def get_coinwren() -> AsyncIterator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient(
        base_url=settings.coinwren_url,
        headers={
            "Authorization": f"Bearer {settings.coinwren_api_key}"
        },
        timeout=10,
    ) as client:
        yield client


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CoinwrenDep = Annotated[httpx2.AsyncClient, Depends(get_coinwren)]


def to_room(row: RoomRow) -> Room:
    return Room(
        id=row.id,
        name=row.name,
        hourly_rate=Money(
            amount=row.hourly_rate_cents, currency=row.currency
        ),
        hours=OpeningHours(
            opens=row.opens_at, closes=row.closes_at
        ),
    )


@app.post("/rooms/{room_id}/holds", status_code=201)
async def hold_room(
    room_id: str, body: HoldIn, session: SessionDep
) -> BookingOut:
    row = await session.get(RoomRow, room_id)
    if row is None:
        raise HTTPException(404, "Room not found")
    room = to_room(row)
    slot = TimeSlot(
        start=body.start.astimezone(UTC),
        end=body.end.astimezone(UTC),
    )
    if not room.hours.contain(slot):
        raise HTTPException(422, "Room is closed at that time")
    now = datetime.now(UTC)
    clash = await session.scalar(
        select(BookingRow.id)
        .where(
            BookingRow.room_id == room_id,
            BookingRow.starts_at < slot.end,
            BookingRow.ends_at > slot.start,
            or_(
                BookingRow.status == "CONFIRMED",
                and_(
                    BookingRow.status == "HELD",
                    BookingRow.created_at >= hold_cutoff(now),
                ),
            ),
        )
        .limit(1)
    )
    if clash is not None:
        raise HTTPException(409, "Room is already booked")
    price = room.price_for(slot)
    booking = BookingRow(
        room_id=room.id,
        member_id=body.member_id,
        starts_at=slot.start,
        ends_at=slot.end,
        price_cents=price.amount,
        currency=price.currency,
    )
    session.add(booking)
    await session.commit()
    return BookingOut.model_validate(booking)


@app.post("/bookings/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str, session: SessionDep, coinwren: CoinwrenDep
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
    response = await coinwren.post(
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
