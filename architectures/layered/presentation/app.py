from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime, time

from fastapi import FastAPI

from data_access.database import (
    create_schema,
    make_engine,
    make_sessions,
)
from data_access.models import Room
from presentation import api
from services.booking_service import utc_now


def create_app(
    *, clock: Callable[[], datetime] = utc_now
) -> FastAPI:
    engine = make_engine()
    sessions = make_sessions(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await create_schema(engine)
        async with sessions() as session:
            session.add(
                Room(
                    id="atlas",
                    name="Atlas",
                    hourly_rate=2400,
                    currency="EUR",
                    opens=time(8),
                    closes=time(20),
                )
            )
            await session.commit()
        yield
        await engine.dispose()

    app = FastAPI(title="Room holds, layered", lifespan=lifespan)
    app.state.sessions = sessions
    app.state.clock = clock
    app.include_router(api.router)
    return app
