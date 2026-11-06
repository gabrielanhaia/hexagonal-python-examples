"""HoldRoom with in-memory adapters: no database, fixed time."""

from datetime import UTC, datetime, time, timedelta

import pytest

from app.adapters.memory import (
    InMemoryBookingRepository,
    InMemoryRoomRepository,
)
from app.application.hold_room import HoldRoom, HoldRoomCommand
from app.domain.errors import RoomNotFound, SlotUnavailable
from app.domain.room import OpeningHours, Room
from app.domain.values import Money

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
ATLAS = Room(
    id="atlas",
    name="Atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    hours=OpeningHours(opens=time(8), closes=time(20)),
)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def command(
    start: int, end: int, room: str = "atlas"
) -> HoldRoomCommand:
    return HoldRoomCommand(
        room_id=room,
        member_id="m-1",
        start=datetime(2026, 11, 10, start, tzinfo=UTC),
        end=datetime(2026, 11, 10, end, tzinfo=UTC),
    )


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def hold(clock: FixedClock) -> HoldRoom:
    return HoldRoom(
        rooms=InMemoryRoomRepository([ATLAS]),
        bookings=InMemoryBookingRepository(),
        clock=clock,
    )


async def test_holds_a_free_slot(hold: HoldRoom) -> None:
    booking = await hold(command(10, 12))

    assert booking.price == Money(amount=4800, currency="EUR")


async def test_an_unknown_room_is_not_found(hold: HoldRoom) -> None:
    with pytest.raises(RoomNotFound):
        await hold(command(10, 11, room="nowhere"))


async def test_a_live_hold_blocks_the_slot(hold: HoldRoom) -> None:
    await hold(command(10, 12))

    with pytest.raises(SlotUnavailable):
        await hold(command(11, 13))


async def test_an_expired_hold_does_not(
    hold: HoldRoom, clock: FixedClock
) -> None:
    await hold(command(10, 12))
    clock.current = NOW + timedelta(minutes=16)

    booking = await hold(command(11, 13))

    assert booking.slot.start.hour == 11
