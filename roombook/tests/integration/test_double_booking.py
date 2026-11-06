"""Two members, one slot, the same instant: the database decides."""

import asyncio
from typing import Self, override

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    FixedClock,
)
from roombook.adapters.outbound.sqlalchemy.mappers import (
    room_to_record,
)
from roombook.adapters.outbound.sqlalchemy.records import (
    BookingRecord,
)
from roombook.adapters.outbound.sqlalchemy.repositories import (
    SqlAlchemyBookingRepository,
)
from roombook.adapters.outbound.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from roombook.adapters.outbound.system import Uuid7Ids
from roombook.application.hold_room import (
    HoldReceipt,
    HoldRoom,
    HoldRoomCommand,
)
from roombook.domain.booking import Booking
from roombook.domain.errors import SlotUnavailable
from roombook.domain.ids import MemberId, RoomId
from roombook.domain.time_slot import TimeSlot
from tests.support import ADA, GRACE, NOW, at, atlas

pytestmark = pytest.mark.postgres

type Sessions = async_sessionmaker[AsyncSession]


class CheckThenWait(SqlAlchemyBookingRepository):
    """Pauses after the overlap check until both callers arrive."""

    def __init__(
        self, session: AsyncSession, barrier: asyncio.Barrier
    ) -> None:
        super().__init__(session)
        self._barrier = barrier

    @override
    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        found = await super().overlapping(room_id, slot)
        await self._barrier.wait()
        return found


class RacingUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(
        self, sessions: Sessions, barrier: asyncio.Barrier
    ) -> None:
        super().__init__(sessions)
        self._barrier = barrier

    @override
    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.bookings = CheckThenWait(self._session, self._barrier)
        return self


async def test_the_exclusion_constraint_wins_the_race(
    sessions: Sessions,
) -> None:
    async with sessions.begin() as session:
        session.add(room_to_record(atlas()))
    barrier = asyncio.Barrier(2)
    hold_room = HoldRoom(
        unit_of_work=lambda: RacingUnitOfWork(sessions, barrier),
        payments=FakePaymentGateway(),
        clock=FixedClock(NOW),
        ids=Uuid7Ids(),
    )

    def ten_to_eleven(member: MemberId) -> HoldRoomCommand:
        return HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=member,
            start=at("10:00"),
            end=at("11:00"),
        )

    results = await asyncio.gather(
        hold_room(ten_to_eleven(ADA)),
        hold_room(ten_to_eleven(GRACE)),
        return_exceptions=True,
    )

    winners = [r for r in results if isinstance(r, HoldReceipt)]
    losers = [r for r in results if isinstance(r, SlotUnavailable)]
    assert len(winners) == 1
    assert len(losers) == 1
    assert isinstance(losers[0].__cause__, IntegrityError)
    async with sessions() as session:
        rows = await session.scalar(
            select(func.count()).select_from(BookingRecord)
        )
    assert rows == 1
