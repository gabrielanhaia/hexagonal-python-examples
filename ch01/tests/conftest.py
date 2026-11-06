import os
import tempfile
from collections.abc import AsyncIterator, Iterator
from datetime import time
from pathlib import Path

import httpx2
import pytest

_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["ROOMBOOK_DATABASE_URL"] = f"sqlite+aiosqlite:///{_db}"

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app, get_coinwren  # noqa: E402
from app.models import Base, Room  # noqa: E402


@pytest.fixture
def charges() -> list[httpx2.Request]:
    return []


@pytest.fixture
def coinwren(
    charges: list[httpx2.Request],
) -> Iterator[None]:
    def handler(request: httpx2.Request) -> httpx2.Response:
        charges.append(request)
        return httpx2.Response(201, json={"id": "ch_1"})

    async def fake() -> AsyncIterator[httpx2.AsyncClient]:
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler),
            base_url="https://coinwren.test",
        ) as client:
            yield client

    app.dependency_overrides[get_coinwren] = fake
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(
    coinwren: None,
) -> AsyncIterator[httpx2.AsyncClient]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        session.add(
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
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client
    await engine.dispose()
