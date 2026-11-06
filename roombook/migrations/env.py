"""Run Alembic migrations over the async psycopg engine."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from roombook.adapters.outbound.sqlalchemy.records import Base
from roombook.settings import Settings

config = context.config
if config.config_file_name is not None:
    fileConfig(
        config.config_file_name, disable_existing_loggers=False
    )


def database_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    return url or Settings().database_url


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=Base.metadata
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(database_url())
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


asyncio.run(run_async_migrations())
