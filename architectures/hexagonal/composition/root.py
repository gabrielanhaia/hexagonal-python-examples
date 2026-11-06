from datetime import time

from fastapi import FastAPI

from adapters import http
from adapters.clock import SystemClock
from adapters.memory import (
    InMemoryBookingRepository,
    InMemoryRoomRepository,
)
from application.cancel_booking import CancelBooking
from application.hold_room import HoldRoom
from application.ports import Clock
from domain.room import OpeningHours, Room
from domain.values import Money

ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


def create_app(*, clock: Clock | None = None) -> FastAPI:
    rooms = InMemoryRoomRepository([ATLAS])
    bookings = InMemoryBookingRepository()
    app = FastAPI(title="Room holds, hexagonal")
    app.state.hold_room = HoldRoom(rooms=rooms, bookings=bookings)
    app.state.cancel_booking = CancelBooking(
        bookings=bookings, clock=clock or SystemClock()
    )
    app.include_router(http.router)
    return app
