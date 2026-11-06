import pytest

from roombook.adapters.outbound.memory.fakes import (
    RecordingNotifier,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.confirm_booking import (
    ConfirmBooking,
    ConfirmBookingCommand,
)
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.booking import BookingStatus
from roombook.domain.errors import BookingNotFound
from roombook.domain.events import BookingConfirmed
from roombook.domain.ids import BookingId, RoomId
from tests.support import ADA, at


async def test_confirms_a_paid_hold_and_tells_the_member(
    hold_room: HoldRoom,
    confirm_booking: ConfirmBooking,
    store: InMemoryStore,
    notifier: RecordingNotifier,
) -> None:
    receipt = await hold_room(
        HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=ADA,
            start=at("10:00"),
            end=at("11:00"),
        )
    )

    await confirm_booking(
        ConfirmBookingCommand(
            booking_id=receipt.booking_id, payment_id="pay-1"
        )
    )

    booking = store.bookings[receipt.booking_id]
    assert booking.status is BookingStatus.CONFIRMED
    assert [type(e) for e in notifier.sent] == [BookingConfirmed]
    assert isinstance(store.outbox[-1], BookingConfirmed)


async def test_an_unknown_booking_is_not_found(
    confirm_booking: ConfirmBooking,
) -> None:
    with pytest.raises(BookingNotFound):
        await confirm_booking(
            ConfirmBookingCommand(
                booking_id=BookingId("missing"), payment_id="pay-1"
            )
        )
