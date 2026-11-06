"""What mapping the domain class itself costs, measured."""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from sqlalchemy import Column, Integer, Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import registry

from roombook.adapters.outbound.sqlalchemy import imperative
from roombook.adapters.outbound.sqlalchemy.mappers import (
    room_to_record,
)
from roombook.domain.booking import Booking, BookingStatus
from roombook.domain.ids import BookingId
from tests.support import ADA, NOW, atlas, slot

BOOKING_ID = BookingId("00000000-0000-7000-8000-000000000001")


@pytest.fixture
def mapped() -> Iterator[None]:
    try:
        imperative.start_mappers()
        yield
    finally:
        imperative.dispose()


@pytest.mark.postgres
@pytest.mark.usefixtures("mapped")
async def test_the_domain_class_round_trips_through_the_orm(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions.begin() as session:
        session.add(room_to_record(atlas()))
    booking = Booking.hold(
        booking_id=BOOKING_ID,
        room=atlas(),
        member_id=ADA,
        slot=slot("10:00", "11:00"),
        now=NOW,
    )

    async with sessions.begin() as session:
        session.add(booking)

    async with sessions() as session:
        loaded = await session.get(Booking, BOOKING_ID)

    assert loaded is not None
    assert loaded.slot == slot("10:00", "11:00")
    assert loaded.price == booking.price
    assert loaded.status is BookingStatus.HELD
    assert loaded.pull_events() == []


def test_a_slotted_dataclass_cannot_be_mapped() -> None:
    local = registry()

    @dataclass(slots=True)
    class Slotted:
        id: int

    table = Table(
        "slotted",
        local.metadata,
        Column("id", Integer, primary_key=True),
    )
    local.map_imperatively(Slotted, table)
    try:
        with pytest.raises(TypeError, match="weak reference"):
            Slotted(id=1)
    finally:
        local.dispose()
