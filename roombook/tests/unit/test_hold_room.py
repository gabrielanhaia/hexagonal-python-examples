import pytest

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.booking import BookingStatus
from roombook.domain.errors import RoomNotFound, SlotUnavailable
from roombook.domain.events import BookingHeld
from roombook.domain.ids import MemberId, RoomId
from roombook.domain.money import Money
from tests.support import ADA, GRACE, at


def command(
    member: MemberId = ADA, room: str = "atlas"
) -> HoldRoomCommand:
    return HoldRoomCommand(
        room_id=RoomId(room),
        member_id=member,
        start=at("10:00"),
        end=at("11:00"),
    )


async def test_holds_a_free_slot_and_opens_a_checkout(
    hold_room: HoldRoom,
    store: InMemoryStore,
    payments: FakePaymentGateway,
) -> None:
    receipt = await hold_room(command())

    booking = store.bookings[receipt.booking_id]
    assert booking.status is BookingStatus.HELD
    assert receipt.price == Money(4000, "EUR")
    assert payments.checkouts == {receipt.booking_id: receipt.price}
    assert [type(e) for e in store.outbox] == [BookingHeld]


async def test_refuses_a_slot_someone_else_holds(
    hold_room: HoldRoom, store: InMemoryStore
) -> None:
    await hold_room(command(ADA))
    with pytest.raises(SlotUnavailable, match="not free"):
        await hold_room(command(GRACE))
    assert len(store.bookings) == 1


async def test_refuses_a_room_that_does_not_exist(
    hold_room: HoldRoom, store: InMemoryStore
) -> None:
    with pytest.raises(RoomNotFound):
        await hold_room(command(room="nowhere"))
    assert store.bookings == {}
    assert store.outbox == []
