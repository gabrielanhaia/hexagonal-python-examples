import json
import os
import tempfile
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
)
from dataclasses import dataclass, field
from datetime import time, timedelta
from pathlib import Path

import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["ROOMBOOK_DATABASE_URL"] = f"sqlite+aiosqlite:///{_db}"

from app.adapters.coinwren import get_coinwren  # noqa: E402
from app.adapters.sqlalchemy.database import (  # noqa: E402
    SessionLocal,
    engine,
)
from app.adapters.sqlalchemy.records import (  # noqa: E402
    Base,
    BookingRow,
    RoomRow,
)
from app.main import app  # noqa: E402

type AgeHold = Callable[[str, int], Awaitable[None]]


@dataclass
class FakeCoinwren:
    declines: bool = False
    requests: list[httpx2.Request] = field(default_factory=list)

    @property
    def charges(self) -> list[object]:
        return [json.loads(r.content) for r in self.requests]

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        if self.declines:
            return httpx2.Response(402, json={"error": "declined"})
        self.requests.append(request)
        return httpx2.Response(
            201, json={"id": f"ch_{len(self.requests)}"}
        )


@pytest.fixture
def coinwren() -> Iterator[FakeCoinwren]:
    fake = FakeCoinwren()

    async def client() -> AsyncIterator[httpx2.AsyncClient]:
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(fake.handle),
            base_url="https://coinwren.test",
        ) as client:
            yield client

    app.dependency_overrides[get_coinwren] = client
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture
def charges(coinwren: FakeCoinwren) -> list[httpx2.Request]:
    return coinwren.requests


async def reset_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        session.add(
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


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    await reset_database()
    async with SessionLocal() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(
    coinwren: FakeCoinwren,
) -> AsyncIterator[httpx2.AsyncClient]:
    await reset_database()
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client
    await engine.dispose()


@pytest.fixture
def age_hold() -> AgeHold:
    async def age(booking_id: str, minutes: int) -> None:
        async with SessionLocal() as session:
            booking = await session.get(BookingRow, booking_id)
            assert booking is not None
            booking.created_at -= timedelta(minutes=minutes)
            await session.commit()

    return age
