import pytest

from roombook.adapters.outbound.memory.fakes import (
    RecordingNotifier,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.cancel_booking import (
    CancelBooking,
    CancelBookingCommand,
)
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.booking import BookingStatus
from roombook.domain.errors import BookingNotFound
from roombook.domain.events import BookingCancelled
from roombook.domain.ids import BookingId, MemberId, RoomId
from roombook.domain.money import Money
from tests.support import ADA, GRACE, at


async def hold(hold_room: HoldRoom) -> BookingId:
    receipt = await hold_room(
        HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=ADA,
            start=at("10:00"),
            end=at("11:00"),
        )
    )
    return receipt.booking_id


def by(
    member: MemberId, booking_id: BookingId
) -> CancelBookingCommand:
    return CancelBookingCommand(
        booking_id=booking_id, member_id=member
    )


async def test_the_member_cancels_their_own_hold(
    hold_room: HoldRoom,
    cancel_booking: CancelBooking,
    store: InMemoryStore,
    notifier: RecordingNotifier,
) -> None:
    booking_id = await hold(hold_room)

    terms = await cancel_booking(by(ADA, booking_id))

    booking = store.bookings[booking_id]
    assert terms.fee == Money(0, "EUR")
    assert booking.status is BookingStatus.CANCELLED
    assert [type(e) for e in notifier.sent] == [BookingCancelled]


async def test_another_member_cannot_see_the_booking(
    hold_room: HoldRoom,
    cancel_booking: CancelBooking,
    store: InMemoryStore,
) -> None:
    booking_id = await hold(hold_room)

    with pytest.raises(BookingNotFound):
        await cancel_booking(by(GRACE, booking_id))
    assert store.bookings[booking_id].status is BookingStatus.HELD
