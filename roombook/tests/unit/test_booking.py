from datetime import timedelta

import pytest

from roombook.domain.booking import Booking, BookingStatus
from roombook.domain.errors import (
    IllegalTransition,
    InvalidTimeSlot,
)
from roombook.domain.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingHeld,
    HoldExpired,
)
from roombook.domain.ids import BookingId
from roombook.domain.money import Money
from tests.support import ADA, NOW, at, atlas, slot

ONE_MINUTE = timedelta(minutes=1)
HOLD = timedelta(minutes=15)


def held(start: str = "10:00", end: str = "11:00") -> Booking:
    booking = Booking.hold(
        booking_id=BookingId("b-1"),
        room=atlas(),
        member_id=ADA,
        slot=slot(start, end),
        now=NOW,
    )
    booking.pull_events()
    return booking


def confirmed() -> Booking:
    booking = held()
    booking.confirm("pay-1", NOW + ONE_MINUTE)
    booking.pull_events()
    return booking


def test_a_hold_prices_the_slot_and_expires_in_15_minutes() -> None:
    booking = Booking.hold(
        booking_id=BookingId("b-1"),
        room=atlas(),
        member_id=ADA,
        slot=slot("10:00", "11:30"),
        now=NOW,
    )
    assert booking.status is BookingStatus.HELD
    assert booking.price == Money(6000, "EUR")
    assert booking.expires_at == NOW + HOLD
    [event] = booking.pull_events()
    assert isinstance(event, BookingHeld)
    assert event.expires_at == NOW + HOLD


def test_cannot_hold_a_slot_that_has_started() -> None:
    with pytest.raises(InvalidTimeSlot, match="future"):
        Booking.hold(
            booking_id=BookingId("b-1"),
            room=atlas(),
            member_id=ADA,
            slot=slot("08:00", "09:00", day="2026-11-30"),
            now=NOW,
        )


def test_confirming_a_hold_records_the_payment() -> None:
    booking = held()
    booking.confirm("pay-1", NOW + ONE_MINUTE)
    assert booking.status is BookingStatus.CONFIRMED
    assert booking.payment_id == "pay-1"
    [event] = booking.pull_events()
    assert isinstance(event, BookingConfirmed)


def test_the_same_payment_confirms_only_once() -> None:
    booking = confirmed()
    booking.confirm("pay-1", NOW + 2 * ONE_MINUTE)
    assert booking.pull_events() == []


def test_a_second_payment_cannot_confirm_again() -> None:
    booking = confirmed()
    with pytest.raises(IllegalTransition, match="cannot become"):
        booking.confirm("pay-2", NOW + 2 * ONE_MINUTE)


def test_a_payment_after_the_hold_expired_is_refused() -> None:
    booking = held()
    with pytest.raises(IllegalTransition, match="expired at"):
        booking.confirm("pay-1", NOW + HOLD)


def test_cancelling_an_unpaid_hold_costs_nothing() -> None:
    terms = held().cancel(NOW + ONE_MINUTE)
    assert terms.fee == Money(0, "EUR")
    assert terms.refund == Money(0, "EUR")


def test_cancelling_a_paid_booking_late_keeps_half() -> None:
    booking = confirmed()
    terms = booking.cancel(at("09:00"))
    assert booking.status is BookingStatus.CANCELLED
    assert terms.fee == Money(2000, "EUR")
    [event] = booking.pull_events()
    assert isinstance(event, BookingCancelled)
    assert event.refund == Money(2000, "EUR")


def test_a_booking_that_has_started_cannot_be_cancelled() -> None:
    with pytest.raises(IllegalTransition, match="already started"):
        confirmed().cancel(at("10:00"))


def test_a_hold_cannot_expire_early() -> None:
    with pytest.raises(IllegalTransition, match="runs until"):
        held().expire(NOW + HOLD - ONE_MINUTE)


def test_a_stale_hold_expires() -> None:
    booking = held()
    booking.expire(NOW + HOLD)
    assert booking.status is BookingStatus.EXPIRED
    [event] = booking.pull_events()
    assert isinstance(event, HoldExpired)


@pytest.mark.parametrize(
    "finished", [BookingStatus.CANCELLED, BookingStatus.EXPIRED]
)
def test_a_finished_booking_accepts_no_transition(
    finished: BookingStatus,
) -> None:
    booking = held()
    booking.status = finished
    later = NOW + HOLD
    for transition in (
        lambda: booking.confirm("pay-1", later),
        lambda: booking.cancel(later),
        lambda: booking.expire(later),
    ):
        with pytest.raises(IllegalTransition):
            transition()


def test_bookings_are_equal_by_id() -> None:
    assert held() == confirmed()
