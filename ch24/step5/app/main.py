"""The composition root: build the app, wire the adapters."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import time

from fastapi import FastAPI

from app.adapters import http
from app.adapters.sqlalchemy.database import SessionLocal, engine
from app.adapters.sqlalchemy.records import Base, RoomRow


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
app.include_router(http.router)
