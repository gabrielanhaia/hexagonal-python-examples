"""The composition roots build the graph; every error is mapped."""

import pytest

from roombook.adapters.inbound.cli.commands import EXIT_CODES
from roombook.adapters.inbound.http.problems import PROBLEMS
from roombook.adapters.outbound.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from roombook.application.ports import PaymentUnavailable
from roombook.composition import Roombook, database, roombook
from roombook.composition_dishka import make_roombook_container
from roombook.domain.errors import BookingError
from roombook.settings import Settings

SETTINGS = Settings(
    database_url="postgresql+psycopg://user:secret@nowhere/db"
)
REFUSALS = [*BookingError.__subclasses__(), PaymentUnavailable]


async def test_the_manual_root_wires_every_use_case() -> None:
    async with (
        database(SETTINGS) as sessions,
        roombook(SETTINGS, sessions) as wired,
    ):
        uow = wired.hold_room.unit_of_work()

    assert isinstance(uow, SqlAlchemyUnitOfWork)


async def test_dishka_builds_the_same_graph() -> None:
    container = make_roombook_container(SETTINGS)
    try:
        wired = await container.get(Roombook)
        uow = wired.cancel_booking.unit_of_work()
    finally:
        await container.close()

    assert isinstance(uow, SqlAlchemyUnitOfWork)


@pytest.mark.parametrize("error", REFUSALS)
def test_every_refusal_has_an_http_status_and_an_exit_code(
    error: type[Exception],
) -> None:
    assert error in PROBLEMS
    assert error in EXIT_CODES
