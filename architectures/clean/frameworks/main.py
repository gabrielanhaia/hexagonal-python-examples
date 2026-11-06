from datetime import time

from fastapi import FastAPI

from entities.room import OpeningHours, Room
from entities.values import Money
from frameworks import web
from frameworks.clock import SystemClock
from interface_adapters.gateways import (
    InMemoryBookingGateway,
    InMemoryRoomGateway,
)
from use_cases.gateways import Clock

ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


def create_app(*, clock: Clock | None = None) -> FastAPI:
    app = FastAPI(title="Room holds, Clean Architecture")
    app.state.gateways = web.Gateways(
        rooms=InMemoryRoomGateway([ATLAS]),
        bookings=InMemoryBookingGateway(),
        clock=clock or SystemClock(),
    )
    app.include_router(web.router)
    return app
