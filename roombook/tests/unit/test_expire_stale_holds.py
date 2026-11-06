from datetime import timedelta

from roombook.adapters.outbound.memory.fakes import (
    FixedClock,
    RecordingNotifier,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.expire_stale_holds import ExpireStaleHolds
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.booking import BookingStatus
from roombook.domain.events import HoldExpired
from roombook.domain.ids import BookingId, RoomId
from tests.support import ADA, at


async def hold(
    hold_room: HoldRoom, start: str, end: str
) -> BookingId:
    receipt = await hold_room(
        HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=ADA,
            start=at(start),
            end=at(end),
        )
    )
    return receipt.booking_id


async def test_expires_only_holds_older_than_15_minutes(
    hold_room: HoldRoom,
    expire_stale_holds: ExpireStaleHolds,
    store: InMemoryStore,
    clock: FixedClock,
    notifier: RecordingNotifier,
) -> None:
    stale = await hold(hold_room, "10:00", "11:00")
    clock.advance(timedelta(minutes=10))
    fresh = await hold(hold_room, "12:00", "13:00")
    clock.advance(timedelta(minutes=5))

    expired = await expire_stale_holds()

    assert expired == 1
    assert store.bookings[stale].status is BookingStatus.EXPIRED
    assert store.bookings[fresh].status is BookingStatus.HELD
    assert [type(e) for e in notifier.sent] == [HoldExpired]
