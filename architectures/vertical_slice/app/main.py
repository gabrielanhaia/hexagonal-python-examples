from datetime import time

from fastapi import FastAPI

from features.cancel_booking import endpoint as cancel_booking
from features.hold_room import endpoint as hold_room
from kernel.database import Database, RoomRow
from kernel.dependencies import Clock, utc_now


def create_app(*, clock: Clock = utc_now) -> FastAPI:
    app = FastAPI(title="Room holds, vertical slices")
    app.state.database = Database(
        rooms={
            "atlas": RoomRow(
                id="atlas",
                name="Atlas",
                hourly_rate=2400,
                currency="EUR",
                opens=time(8),
                closes=time(20),
            )
        }
    )
    app.state.clock = clock
    app.include_router(hold_room.router)
    app.include_router(cancel_booking.router)
    return app
