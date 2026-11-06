"""PostgreSQL for the tests marked `postgres`, started once."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:18.6-trixie"
ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"
TABLES = "rooms, bookings, outbox, processed_messages"


def migrate(database_url: str) -> None:
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as pg:
        url = pg.get_connection_url()
        migrate(url)
        yield url


@pytest.fixture
async def sessions(
    database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """An empty, migrated schema for every test."""
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES}"))
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()
