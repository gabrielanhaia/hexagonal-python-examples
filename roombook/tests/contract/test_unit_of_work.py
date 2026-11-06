"""One contract, two adapters: in-memory and PostgreSQL."""

from datetime import timedelta

import pytest

from roombook.domain.booking import Booking, BookingStatus
from roombook.domain.errors import SlotUnavailable
from roombook.domain.ids import BookingId, RoomId
from roombook.domain.time_slot import TimeSlot
from tests.contract.backends import Backend
from tests.support import ADA, NOW, atlas, slot

TEN_TO_ELEVEN = slot("10:00", "11:00")
FIRST = BookingId("00000000-0000-7000-8000-000000000001")
SECOND = BookingId("00000000-0000-7000-8000-000000000002")


def hold(
    booking_id: BookingId = FIRST,
    during: TimeSlot = TEN_TO_ELEVEN,
) -> Booking:
    return Booking.hold(
        booking_id=booking_id,
        room=atlas(),
        member_id=ADA,
        slot=during,
        now=NOW,
    )


async def given(backend: Backend, *bookings: Booking) -> None:
    async with backend.unit_of_work() as uow:
        for booking in bookings:
            await uow.bookings.add(booking)
        await uow.commit()


async def test_a_committed_booking_reads_back_unchanged(
    backend: Backend,
) -> None:
    await given(backend, hold())

    async with backend.unit_of_work() as uow:
        loaded = await uow.bookings.get(FIRST)

    assert loaded is not None
    assert (loaded.room_id, loaded.member_id) == ("atlas", ADA)
    assert loaded.slot == slot("10:00", "11:00")
    assert loaded.price == hold().price
    assert loaded.status is BookingStatus.HELD
    assert loaded.held_at == NOW
    assert loaded.pull_events() == []


async def test_an_unknown_id_reads_as_none(
    backend: Backend,
) -> None:
    async with backend.unit_of_work() as uow:
        assert await uow.bookings.get(FIRST) is None


async def test_nothing_persists_without_commit(
    backend: Backend,
) -> None:
    async with backend.unit_of_work() as uow:
        await uow.bookings.add(hold())

    async with backend.unit_of_work() as uow:
        assert await uow.bookings.get(FIRST) is None


async def test_save_persists_a_transition(backend: Backend) -> None:
    await given(backend, hold())

    async with backend.unit_of_work() as uow:
        booking = await uow.bookings.get(FIRST)
        assert booking is not None
        booking.confirm("pay-1", NOW)
        await uow.bookings.save(booking)
        await uow.commit()

    async with backend.unit_of_work() as uow:
        reloaded = await uow.bookings.get(FIRST)
    assert reloaded is not None
    assert reloaded.status is BookingStatus.CONFIRMED
    assert reloaded.payment_id == "pay-1"


async def test_a_change_without_save_is_not_persisted(
    backend: Backend,
) -> None:
    await given(backend, hold())

    async with backend.unit_of_work() as uow:
        booking = await uow.bookings.get(FIRST)
        assert booking is not None
        booking.confirm("pay-1", NOW)
        await uow.commit()

    async with backend.unit_of_work() as uow:
        reloaded = await uow.bookings.get(FIRST)
    assert reloaded is not None
    assert reloaded.status is BookingStatus.HELD


async def test_overlapping_finds_only_active_bookings_that_overlap(
    backend: Backend,
) -> None:
    cancelled = hold(SECOND, slot("12:00", "13:00"))
    cancelled.cancel(NOW)
    await given(backend, hold(), cancelled)

    async with backend.unit_of_work() as uow:
        found = await uow.bookings.overlapping(
            RoomId("atlas"), slot("10:45", "12:30")
        )
        back_to_back = await uow.bookings.overlapping(
            RoomId("atlas"), slot("11:00", "12:00")
        )

    assert [booking.id for booking in found] == [FIRST]
    assert back_to_back == []


async def test_an_overlapping_active_booking_is_refused(
    backend: Backend,
) -> None:
    await given(backend, hold())

    with pytest.raises(SlotUnavailable):
        await given(backend, hold(SECOND, slot("10:30", "11:30")))


async def test_a_cancelled_booking_frees_its_slot(
    backend: Backend,
) -> None:
    cancelled = hold()
    cancelled.cancel(NOW)
    await given(backend, cancelled)

    await given(backend, hold(SECOND))


async def test_stale_holds_are_the_ones_15_minutes_old(
    backend: Backend,
) -> None:
    await given(backend, hold())
    just_before = NOW + timedelta(minutes=14)
    on_time = NOW + timedelta(minutes=15)

    async with backend.unit_of_work() as uow:
        early = await uow.bookings.stale_holds(just_before)
        due = await uow.bookings.stale_holds(on_time)

    assert early == []
    assert [booking.id for booking in due] == [FIRST]


async def test_rooms_read_back_by_id(backend: Backend) -> None:
    async with backend.unit_of_work() as uow:
        assert await uow.rooms.get(RoomId("atlas")) == atlas()
        assert await uow.rooms.get(RoomId("nowhere")) is None


async def test_outbox_events_commit_with_the_booking(
    backend: Backend,
) -> None:
    async with backend.unit_of_work() as uow:
        booking = hold()
        await uow.bookings.add(booking)
        await uow.outbox.put(booking.pull_events())

    assert await backend.outbox_types() == []

    async with backend.unit_of_work() as uow:
        booking = hold()
        await uow.bookings.add(booking)
        await uow.outbox.put(booking.pull_events())
        await uow.commit()

    assert await backend.outbox_types() == ["BookingHeld"]


async def test_a_processed_message_is_remembered_once(
    backend: Backend,
) -> None:
    processed = backend.processed_messages()

    assert not await processed.seen("evt-1")
    await processed.remember("evt-1")
    await processed.remember("evt-1")
    assert await processed.seen("evt-1")
