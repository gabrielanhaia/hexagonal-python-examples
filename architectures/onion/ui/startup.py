from datetime import time

from fastapi import FastAPI

from application_services.booking_service import (
    BookingApplicationService,
)
from application_services.clock import Clock
from domain_model.room import OpeningHours, Room
from domain_model.values import Money
from domain_services.availability import AvailabilityService
from infrastructure.clock import SystemClock
from infrastructure.memory import (
    InMemoryBookingRepository,
    InMemoryRoomRepository,
)
from ui import api

ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


def create_app(*, clock: Clock | None = None) -> FastAPI:
    bookings = InMemoryBookingRepository()
    app = FastAPI(title="Room holds, onion")
    app.state.bookings = BookingApplicationService(
        rooms=InMemoryRoomRepository([ATLAS]),
        bookings=bookings,
        availability=AvailabilityService(bookings),
        clock=clock or SystemClock(),
    )
    app.include_router(api.router)
    return app
